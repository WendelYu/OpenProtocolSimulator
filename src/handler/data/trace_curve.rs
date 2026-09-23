use serde::{Deserialize, Serialize};

/// Trace curve type per Open Protocol specification
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TraceType {
    Angle = 1,
    Torque = 2,
    Current = 3,
    Gradient = 4,
    Stroke = 5,
    Force = 6,
}

impl TraceType {
    pub fn as_u16(&self) -> u16 {
        *self as u16
    }
}

/// Simulation data for a tightening trace curve (MID 0900)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TraceCurveData {
    pub result_id: u64,
    pub timestamp: String,
    pub trace_type: TraceType,
    pub transducer_type: u16,  // 1 = transducer 1
    pub unit: u16,             // 001 = Nm, 002 = Degrees, etc.
    pub time_interval_ms: u32, // Interval between samples (e.g. 2ms)
    pub coefficient: u32,      // Divisor K (PID 02213), e.g. 100 means value/100
    pub samples: Vec<u16>,     // 16-bit binary integer samples (physical = sample / coefficient)
}

impl TraceCurveData {
    /// Generate realistic simulated torque and angle trace curves based on final torque/angle and OK status
    pub fn generate_curves(
        result_id: u64,
        timestamp: &str,
        _target_torque: f64,
        actual_torque: f64,
        actual_angle: f64,
        is_ok: bool,
    ) -> (Self, Self) {
        let sample_count = 150usize;
        let time_interval_ms = 2u32; // 2ms per sample -> 300ms total
        let coefficient = 100u32; // 100 -> 15.00 Nm = 1500 in binary

        let mut torque_samples = Vec::with_capacity(sample_count);
        let mut angle_samples = Vec::with_capacity(sample_count);

        // Stages:
        // 0..30: Free run (low torque ~ 0.5 - 1.2 Nm, angle climbing steadily)
        // 30..60: Run-down / Snug seating (torque goes from 1.2 to ~3.0 Nm, angle climbs)
        // 60..120: Tightening / Elastic deformation (steep climb from 3.0 to actual_torque)
        // 120..150: Peak hold / Shut-off (torque stabilizes around actual_torque)

        let rundown_torque = 1.8f64;
        let snug_torque = 3.5f64.min(actual_torque * 0.35);

        for i in 0..sample_count {
            let (t_val, a_val) = if i < 30 {
                // Free run
                let progress = i as f64 / 30.0;
                let t = 0.2 + progress * (rundown_torque - 0.2) + ((i % 3) as f64 * 0.05);
                let a = progress * (actual_angle * 0.3);
                (t, a)
            } else if i < 60 {
                // Seating
                let progress = (i - 30) as f64 / 30.0;
                let t = rundown_torque + progress * (snug_torque - rundown_torque);
                let a = (actual_angle * 0.3) + progress * (actual_angle * 0.3);
                (t, a)
            } else if i < 120 {
                // Steep tightening stage (S-curve)
                let progress = (i - 60) as f64 / 60.0;
                // Smooth sinusoidal transition
                let factor = (1.0 - (progress * std::f64::consts::PI).cos()) / 2.0;
                let t = snug_torque + factor * (actual_torque - snug_torque);
                let a = (actual_angle * 0.6) + factor * (actual_angle * 0.38);
                (t, a)
            } else {
                // Peak hold & shut-off
                let t = if is_ok {
                    actual_torque
                } else {
                    // Slight overshoot or drop for NOK
                    actual_torque * 1.05
                };
                let a = actual_angle;
                (t, a)
            };

            let t_bin = (t_val.max(0.0) * coefficient as f64).round() as u16;
            let a_bin = (a_val.max(0.0) * 10.0).round() as u16; // Angle scaled x10

            torque_samples.push(t_bin);
            angle_samples.push(a_bin);
        }

        let torque_curve = Self {
            result_id,
            timestamp: timestamp.to_string(),
            trace_type: TraceType::Torque,
            transducer_type: 1,
            unit: 1, // 001 = Nm
            time_interval_ms,
            coefficient,
            samples: torque_samples,
        };

        let angle_curve = Self {
            result_id,
            timestamp: timestamp.to_string(),
            trace_type: TraceType::Angle,
            transducer_type: 1,
            unit: 2, // 002 = Degrees
            time_interval_ms,
            coefficient: 10, // Angle x10
            samples: angle_samples,
        };

        (torque_curve, angle_curve)
    }

    /// Serialize into full MID 0900 byte payload according to Open Protocol specification Table 139
    pub fn serialize_mid_0900(&self, revision: u8) -> Vec<u8> {
        let sample_count = self.samples.len();

        // 1. Build ASCII metadata part
        let mut ascii_part = String::new();

        // Result Data Identifier (10 bytes)
        ascii_part.push_str(&format!("{:010}", self.result_id));

        // Time stamp (19 bytes, YYYY-MM-DD:HH:MM:SS)
        if self.timestamp.len() >= 19 {
            ascii_part.push_str(&self.timestamp[..19]);
        } else {
            ascii_part.push_str(&format!("{:<19}", self.timestamp));
        }

        // Number of PID's on root level (3 bytes) -> 000
        ascii_part.push_str("000");

        // Trace Type (2 bytes) -> 01=Angle, 02=Torque
        ascii_part.push_str(&format!("{:02}", self.trace_type.as_u16()));

        // Transducer Type (2 bytes) -> 01
        ascii_part.push_str(&format!("{:02}", self.transducer_type));

        // Unit (3 bytes) -> 001 for Nm, 002 for deg
        ascii_part.push_str(&format!("{:03}", self.unit));

        // Number of parameter data fields for this trace (3 bytes) -> 001 (PID 02213: Coefficient)
        ascii_part.push_str("001");

        // Variable Data Field for Coefficient:
        // Parameter ID (5 bytes) = 02213
        ascii_part.push_str("02213");
        // Length of data value (3 bytes) = 003 (e.g. 100)
        let coeff_str = format!("{}", self.coefficient);
        ascii_part.push_str(&format!("{:03}", coeff_str.len()));
        // Data Type (2 bytes) = 01 (UI)
        ascii_part.push_str("01");
        // Unit (3 bytes) = 000
        ascii_part.push_str("000");
        // Step no (4 bytes) = 0000
        ascii_part.push_str("0000");
        // Data value (variable)
        ascii_part.push_str(&coeff_str);

        // Number of resolution fields (3 bytes) -> 001
        ascii_part.push_str("001");

        // Resolution field:
        // First index (5 bytes) = 00000
        ascii_part.push_str("00000");
        // Last index (5 bytes) = e.g. 00149
        ascii_part.push_str(&format!("{:05}", sample_count.saturating_sub(1)));
        // Length (3 bytes) = 003
        let interval_str = format!("{}", self.time_interval_ms);
        ascii_part.push_str(&format!("{:03}", interval_str.len()));
        // Data Type (2 bytes) = 01 (UI)
        ascii_part.push_str("01");
        // Unit (3 bytes) = 003 (ms)
        ascii_part.push_str("003");
        // Time value = interval_str
        ascii_part.push_str(&interval_str);

        // Number of trace samples (5 bytes)
        ascii_part.push_str(&format!("{:05}", sample_count));

        // 2. Binary part:
        // Starts with a NUL (0x00) delimiter
        // followed by 2 bytes per sample (big-endian as standard for Open Protocol binary fields)
        let mut binary_part = Vec::with_capacity(1 + sample_count * 2);
        binary_part.push(0x00); // NUL separator before binary trace samples

        for sample in &self.samples {
            binary_part.extend_from_slice(&sample.to_be_bytes());
        }

        // Total message = 20-byte Header + ASCII payload + Binary payload
        let total_length = 20 + ascii_part.len() + binary_part.len();

        let mut packet = Vec::with_capacity(total_length);
        // Header:
        // Length (4 bytes)
        packet.extend_from_slice(format!("{:04}", total_length.min(9999)).as_bytes());
        // MID (4 bytes) = 0900
        packet.extend_from_slice(b"0900");
        // Revision (3 bytes)
        packet.extend_from_slice(format!("{:03}", revision).as_bytes());
        // Reserved/spaces (9 bytes)
        packet.extend_from_slice(b"         ");

        // Body:
        packet.extend_from_slice(ascii_part.as_bytes());
        packet.extend_from_slice(&binary_part);

        packet
    }
}

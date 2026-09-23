export type TraceType = 'Angle' | 'Torque' | 'Current' | 'Gradient' | 'Stroke' | 'Force';

export interface TraceCurveData {
	result_id: number;
	timestamp: string;
	trace_type: TraceType;
	transducer_type: number;
	unit: number;
	time_interval_ms: number;
	coefficient: number;
	samples: number[];
}

export interface LatestCurves {
	result_id: number;
	timestamp: string;
	is_ok: boolean;
	actual_torque: number;
	actual_angle: number;
	torque_curve: TraceCurveData;
	angle_curve: TraceCurveData;
}

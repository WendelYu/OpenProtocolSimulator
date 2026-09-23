use crate::handler::data::CommandAccepted;
use crate::handler::data::error_response::{ErrorCode, ErrorResponse};
use crate::handler::{HandlerContext, HandlerError, HandlerResult, MidHandler};
use crate::protocol::{Message, Response};

/// Handler for MID 0900 direct subscription / upload request
/// Integrators can directly subscribe to MID 0900 (Revision 1..=3)
pub struct TraceCurveDirectSubscriptionHandler;

impl MidHandler for TraceCurveDirectSubscriptionHandler {
    fn handle(&self, message: &Message) -> Result<Response, HandlerError> {
        println!("MID 0900: Trace curve subscription / request accepted");
        let ack_data = CommandAccepted::with_mid(900);
        Ok(Response::from_data(5, message.revision, ack_data))
    }

    fn handle_with_context(
        &self,
        message: &Message,
        context: &mut HandlerContext<'_>,
    ) -> Result<HandlerResult, HandlerError> {
        // Trace type from extra data if present (e.g., "01" or "02")
        let trace_type = if message.data.len() >= 2 {
            let s = String::from_utf8_lossy(&message.data[..2]);
            s.trim().parse::<u8>().unwrap_or(2)
        } else {
            2 // Default: Torque curve
        };

        context
            .subscriptions
            .subscribe_trace_curve(trace_type, message.revision);

        self.handle(message).map(HandlerResult::Response)
    }
}

/// Handler for MID 0008: General subscription envelope (Table 26)
/// Used when subscribing to MID 0900 via MID 0008
pub struct GeneralSubscriptionHandler;

impl MidHandler for GeneralSubscriptionHandler {
    fn handle(&self, message: &Message) -> Result<Response, HandlerError> {
        // Default reply: MID 0005 with the subscribed MID
        let target_mid = if message.data.len() >= 4 {
            let s = String::from_utf8_lossy(&message.data[..4]);
            s.trim().parse::<u32>().unwrap_or(900)
        } else {
            900
        };
        let ack_data = CommandAccepted::with_mid(target_mid);
        Ok(Response::from_data(5, message.revision, ack_data))
    }

    fn handle_with_context(
        &self,
        message: &Message,
        context: &mut HandlerContext<'_>,
    ) -> Result<HandlerResult, HandlerError> {
        // MID 0008 data format:
        // Bytes 0..4 (21..24): Subscribed MID (e.g. "0900")
        // Bytes 4..7 (25..27): Wanted revision (e.g. "001")
        // Bytes 7..9 (28..29): Extra data length (e.g. "05")
        // Bytes 9..  (30..  ): Extra data
        if message.data.len() < 4 {
            return Ok(HandlerResult::Response(Response::from_data(
                4,
                message.revision,
                ErrorResponse::new(message.mid, ErrorCode::InvalidData),
            )));
        }

        let target_mid_str = String::from_utf8_lossy(&message.data[..4]);
        let target_mid = target_mid_str.trim().parse::<u16>().unwrap_or(0);

        if target_mid == 900 {
            let wanted_rev = if message.data.len() >= 7 {
                let rev_str = String::from_utf8_lossy(&message.data[4..7]);
                rev_str.trim().parse::<u16>().unwrap_or(1)
            } else {
                1
            };

            // Check trace type in extra data if available
            // In Table 143: Send alt (1 byte) + Data ID (19 or 10) + Num trace types (2) + Trace type (3)
            let mut trace_type = 2u8; // default Torque
            if message.data.len() >= 10 {
                let extra = String::from_utf8_lossy(&message.data[9..]);
                if extra.contains("001") {
                    trace_type = 1;
                } else if extra.contains("002") {
                    trace_type = 2;
                }
            }

            println!(
                "MID 0008: Subscribing to MID {:04} (rev {}, type {})",
                target_mid, wanted_rev, trace_type
            );
            context
                .subscriptions
                .subscribe_trace_curve(trace_type, wanted_rev);
            self.handle(message).map(HandlerResult::Response)
        } else {
            // Unknown subscription via MID 0008
            Ok(HandlerResult::Response(Response::from_data(
                4,
                message.revision,
                ErrorResponse::new(message.mid, ErrorCode::GenericError),
            )))
        }
    }
}

/// Handler for MID 0009: General unsubscription envelope (Table 27)
/// Used when unsubscribing from MID 0900 via MID 0009
pub struct GeneralUnsubscribeHandler;

impl MidHandler for GeneralUnsubscribeHandler {
    fn handle(&self, message: &Message) -> Result<Response, HandlerError> {
        let target_mid = if message.data.len() >= 4 {
            let s = String::from_utf8_lossy(&message.data[..4]);
            s.trim().parse::<u32>().unwrap_or(900)
        } else {
            900
        };
        let ack_data = CommandAccepted::with_mid(target_mid);
        Ok(Response::from_data(5, message.revision, ack_data))
    }

    fn handle_with_context(
        &self,
        message: &Message,
        context: &mut HandlerContext<'_>,
    ) -> Result<HandlerResult, HandlerError> {
        if message.data.len() < 4 {
            return Ok(HandlerResult::Response(Response::from_data(
                4,
                message.revision,
                ErrorResponse::new(message.mid, ErrorCode::InvalidData),
            )));
        }

        let target_mid_str = String::from_utf8_lossy(&message.data[..4]);
        let target_mid = target_mid_str.trim().parse::<u16>().unwrap_or(0);

        if target_mid == 900 {
            println!("MID 0009: Unsubscribing from MID 0900 trace curve");
            context.subscriptions.unsubscribe_trace_curve();
            self.handle(message).map(HandlerResult::Response)
        } else {
            Ok(HandlerResult::Response(Response::from_data(
                4,
                message.revision,
                ErrorResponse::new(message.mid, ErrorCode::GenericError),
            )))
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::subscriptions::Subscriptions;

    #[test]
    fn test_direct_mid0900_subscription() {
        let handler = TraceCurveDirectSubscriptionHandler;
        let mut subs = Subscriptions::new();
        let mut ctx = HandlerContext::new(&mut subs);

        let msg = Message {
            length: 22,
            mid: 900,
            revision: 1,
            data: b"02".to_vec(),
        };

        let res = handler.handle_with_context(&msg, &mut ctx).unwrap();
        match res {
            HandlerResult::Response(r) => {
                assert_eq!(r.mid, 5);
                assert_eq!(r.data, b"0900");
            }
            _ => panic!("Expected response"),
        }
        assert!(ctx.subscriptions.is_subscribed_to_trace_curve());
        assert_eq!(ctx.subscriptions.trace_curve_type, 2);
    }

    #[test]
    fn test_mid0008_envelope_subscription() {
        let handler = GeneralSubscriptionHandler;
        let mut subs = Subscriptions::new();
        let mut ctx = HandlerContext::new(&mut subs);

        // 0900 (MID) 001 (Rev) 05 (Len) 0001001 (Extra: Type 1 Angle)
        let msg = Message {
            length: 35,
            mid: 8,
            revision: 1,
            data: b"0900001050001001".to_vec(),
        };

        let res = handler.handle_with_context(&msg, &mut ctx).unwrap();
        match res {
            HandlerResult::Response(r) => {
                assert_eq!(r.mid, 5);
                assert_eq!(r.data, b"0900");
            }
            _ => panic!("Expected response"),
        }
        assert!(ctx.subscriptions.is_subscribed_to_trace_curve());
        assert_eq!(ctx.subscriptions.trace_curve_type, 1);
    }

    #[test]
    fn test_mid0009_envelope_unsubscription() {
        let handler = GeneralUnsubscribeHandler;
        let mut subs = Subscriptions::new();
        subs.subscribe_trace_curve(2, 1);
        assert!(subs.is_subscribed_to_trace_curve());

        let mut ctx = HandlerContext::new(&mut subs);

        let msg = Message {
            length: 30,
            mid: 9,
            revision: 1,
            data: b"090000100".to_vec(),
        };

        let res = handler.handle_with_context(&msg, &mut ctx).unwrap();
        match res {
            HandlerResult::Response(r) => {
                assert_eq!(r.mid, 5);
                assert_eq!(r.data, b"0900");
            }
            _ => panic!("Expected response"),
        }
        assert!(!ctx.subscriptions.is_subscribed_to_trace_curve());
    }
}

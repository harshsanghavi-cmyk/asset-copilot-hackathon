export function describeFailure(code='run_failed',detail=''):{code:string;title:string;message:string}{
 if((code==='run_failed'||code==='provider_error')&&/Gemma|provider/i.test(detail)&&/HTTP\s+\d{3}/i.test(detail))code='provider_error';
 if(code==='provider_error'&&/API[ _]key.{0,30}(expired|invalid|not valid)|invalid API[ _]key|API_KEY_(INVALID|EXPIRED)/i.test(detail)){const expired=/expired/i.test(detail);return {code:'provider_credentials',title:'Model access error',message:`Gemma rejected the server credential (${expired?'expired API key':'invalid API key'}). Update the server credential before retrying. Your message is saved.`};}
 const http=detail.match(/HTTP\s+(\d{3})/i)?.[1];
 if(code==='provider_credentials')return {code,title:'Model access error',message:'Gemma rejected the server credential. Update it before retrying. Your message is saved.'};
 if(code==='model_under_repair')return {code,title:'Model connection under repair',message:'Google AI Studio requests are temporarily paused. Your question is saved; history and diagnostics remain available.'};
 if(code==='status_unknown')return {code,title:'Response status unconfirmed',message:'The server response is not yet confirmed. Check status before sending again.'};
 if(code==='cancelled')return {code,title:'Response stopped',message:'You stopped this response. Your request is saved.'};
 if(code==='conversation_changed')return {code,title:'Response stopped',message:'The conversation changed before this response completed. Your request is saved.'};
 if(code==='provider_rate_limited')return {code,title:'Model is busy',message:'Google’s model service is busy. Your question is saved. Try again shortly.'};
 if(code==='provider_error')return {code,title:'Model service error',message:`Gemma rejected the request${http?` (HTTP ${http})`:''}. Your question is saved. Please try again.`};
 if(code==='model_not_configured')return {code,title:'Model service unavailable',message:'Gemma is not configured on the server. Your message is saved.'};
 if(code==='provider_timeout')return {code,title:'Response timed out',message:'The model took too long to respond. Your question is saved.'};
 if(code==='provider_transport_or_shape')return {code,title:'Model connection error',message:'The server could not complete its connection to Gemma. Your message is saved.'};
 if(['integration_generation_limit','attempt_budget'].includes(code))return {code,title:'Request limit reached',message:'The workspace has reached its configured request limit. Your message is saved.'};
 if(code.startsWith('invalid_')||code.startsWith('unsupported_'))return {code,title:'Answer could not be verified',message:'Some details didn’t match the source records. Your question is saved.'};
 if(code==='network'||code==='connection_closed')return {code,title:'Connection interrupted',message:'The connection ended before the response completed. Your request is saved.'};
 if(code==='interrupted')return {code,title:'Response interrupted',message:'No completed response was saved for this request. Your message is preserved; you can try again.'};
 return {code:'run_failed',title:'Response unavailable',message:'We couldn’t finish that response. Your question is saved.'};
}

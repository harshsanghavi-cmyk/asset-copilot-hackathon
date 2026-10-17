import { z } from 'zod';

export const cellSchema = z.union([z.string(), z.number().finite(), z.boolean(), z.null()]);
const optionalText=z.string().nullish().transform(value=>value??undefined);
export const evidenceSchema = z.object({ id: z.string(), title: z.string(), source_kind: z.string(), source_id: z.string(), excerpt: optionalText, path: optionalText, author: optionalText, source_time: optionalText });
export const resultSchema = z.object({ result_set_id: z.string(), knowledge_revision: z.number().int().nonnegative(), dataset_revision: z.string(), columns: z.array(z.object({ key: z.string(), label: z.string(), unit: optionalText })), rows: z.array(z.record(cellSchema)), evidence_ids: z.array(z.string()), coverage: z.object({ evaluated: z.number(), matching: z.number(), unknown: z.number() }).optional() });
export const blockSchema = z.object({ id: z.string(), type: z.enum(['status','table','line','bar','heatmap','map','diagram']), title: z.string(), subtitle: optionalText, result_set_id: z.string(), evidence_ids: z.array(z.string()).min(1), span: z.union([z.literal(1),z.literal(2),z.literal(3)]).optional(), encoding: z.record(z.string()).default({}) });
export const answerSchema = z.object({ schema_version: z.literal('1.0'), answer_id: z.string(), thread_id: z.string(), user_id: z.string(), dataset_namespace: z.string(), dataset_revision: z.string(), knowledge_revision: z.number().int().nonnegative(), reference_date: z.string(), window: z.object({ start: z.string(), end: z.string(), closure: z.string() }).optional(), narrative: z.string(), presentation_only:z.boolean().optional(),source_answer_id:optionalText,layout:z.object({direction:z.enum(['row','column']).optional(),mode:z.enum(['single_row','single_column','grid']).optional()}).optional(), generation:z.object({status:z.enum(['complete','partial','clarification']),verified_tool_data:z.boolean().optional(),explanation_error_code:optionalText,retry_after:z.number().nonnegative().nullish().transform(v=>v??undefined),retry_at:optionalText,model:optionalText,live:z.boolean().optional()}).optional(), blocks: z.array(blockSchema).max(16), results: z.record(resultSchema), evidence: z.record(evidenceSchema), warnings: z.array(z.string()).default([]), sample: z.boolean().default(false) });
export type Evidence = z.infer<typeof evidenceSchema>;
export type ResultSet = z.infer<typeof resultSchema>;
export type AnswerBlock = z.infer<typeof blockSchema>;
export type AnswerEnvelope = z.infer<typeof answerSchema>;
export function validateAnswer(input: unknown, scope: { userId: string; sessionId: string }): AnswerEnvelope {
  const answer = answerSchema.parse(input);
  if (answer.user_id !== scope.userId || answer.thread_id !== scope.sessionId) throw new Error('This answer belongs to a different conversation.');
  if(answer.generation?.status==='partial'&&!answer.generation.verified_tool_data&&(answer.blocks.length>0||Object.keys(answer.results).length>0))throw new Error('Partial data must be explicitly verified by the server.');
  const ids = new Set<string>();
  for (const block of answer.blocks) {
    if(ids.has(block.id)) throw new Error('The answer contains duplicate panel identifiers.'); ids.add(block.id);
    const result = Object.hasOwn(answer.results,block.result_set_id) ? answer.results[block.result_set_id] : undefined;
    if (!result || result.knowledge_revision !== answer.knowledge_revision || result.dataset_revision !== answer.dataset_revision) throw new Error('The answer contains an unavailable or mixed-revision result.');
    if (!block.evidence_ids.every(id => Object.hasOwn(answer.evidence,id))) throw new Error('A source reference could not be verified.');
    const required:Partial<Record<AnswerBlock['type'],string[]>>={status:['label','value'],line:['x','y'],bar:['x','y'],heatmap:['x','y','value'],map:['latitude','longitude'],diagram:['source','target']};
    if((required[block.type]||[]).some(key=>!block.encoding[key]))throw new Error('A panel is missing a required column encoding.');
    if(block.type==='status'){const assetKey=['asset_id','well_id','well'].find(key=>result.columns.some(column=>column.key===key));if(assetKey&&block.encoding.label!==assetKey)throw new Error('A status card must identify the asset using its well or asset ID.');}
    if (!Object.values(block.encoding).every(key => result.columns.some(column=>column.key===key))) throw new Error('A panel refers to an unavailable result column.');
  }
  return answer;
}

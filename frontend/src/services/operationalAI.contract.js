/**
 * Operational AI API contract helpers.
 * Simplified: single execute endpoint, no approval gates.
 */

export const OperationalAIModule = Object.freeze({
    NLP: 'nlp',
    PREDICTIONS: 'predictions',
    FINANCE: 'finance',
    HR: 'hr',
    CHAT: 'chat',
});

export function buildConversationalPayload(message, module = OperationalAIModule.NLP) {
    return { message, module };
}

export function buildOperationalRollbackPayload(executionId) {
    return { execution_id: executionId };
}

export function buildAuditQuery(params = {}) {
    const query = new URLSearchParams();
    const allowed = [
        'module',
        'operation_type',
        'risk_level',
        'actor_user_id',
        'start_date',
        'end_date',
        'limit',
    ];

    allowed.forEach((key) => {
        const val = params[key];
        if (val !== undefined && val !== null && String(val).trim() !== '') {
            query.set(key, String(val));
        }
    });

    return query.toString();
}

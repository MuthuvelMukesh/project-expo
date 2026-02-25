/**
 * Operational AI API contract helpers.
 * Keeps payload keys and endpoint mapping consistent with backend /api/ops-ai.
 */

export const OperationalAIModule = Object.freeze({
    NLP: 'nlp',
    PREDICTIONS: 'predictions',
    FINANCE: 'finance',
    HR: 'hr',
    CHAT: 'chat',
});

export const OperationalDecision = Object.freeze({
    APPROVE: 'APPROVE',
    REJECT: 'REJECT',
    ESCALATE: 'ESCALATE',
});

export function buildOperationalPlanPayload(message, module = OperationalAIModule.NLP, clarification = null) {
    return {
        message,
        module,
        clarification,
    };
}

export function buildOperationalDecisionPayload({
    planId,
    decision,
    approvedIds = [],
    rejectedIds = [],
    comment = null,
    twoFactorCode = null,
}) {
    return {
        plan_id: planId,
        decision,
        approved_ids: approvedIds,
        rejected_ids: rejectedIds,
        comment,
        two_factor_code: twoFactorCode,
    };
}

export function buildOperationalExecutePayload(planId) {
    return { plan_id: planId };
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

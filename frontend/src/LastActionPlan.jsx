/* eslint-disable react/prop-types */
function LastActionPlan({ actionPlan }) {
  return (
    <section className="action-plan-section">
      <h2>Último Plano de Ação Disponível</h2>
      {actionPlan ? (
        <a href={actionPlan.action_plan_url} className="action-plan-link" target="_blank" rel="noopener noreferrer">
          Acessar Plano de Ação
        </a>
      ) : (
        <p>Nenhum plano de ação recente encontrado.</p>
      )}
    </section>
  );
}

export default LastActionPlan;
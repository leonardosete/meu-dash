import React, { useState } from "react";
import { submitFeedback } from "../services/api";
import { FeedbackData } from "../types";
import { MessageSquare, Loader2, X, CheckCircle } from "lucide-react";

interface FeedbackModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const FeedbackModal: React.FC<FeedbackModalProps> = ({ isOpen, onClose }) => {
  const [formData, setFormData] = useState<FeedbackData>({
    type: "suggestion",
    title: "",
    description: "",
    email: "",
    context: "",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<{
    success: boolean;
    message: string;
    issueUrl?: string;
  } | null>(null);

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setSubmitStatus(null);

    try {
      const result = await submitFeedback(formData);
      setSubmitStatus({
        success: true,
        message: result.message,
        issueUrl: result.issue_url,
      });
      // Reset form after successful submission
      setFormData({
        type: "suggestion",
        title: "",
        description: "",
        email: "",
        context: "",
      });
    } catch (error) {
      const apiError = error as { response?: { data?: { error?: string } } };
      setSubmitStatus({
        success: false,
        message: apiError.response?.data?.error || "Erro ao enviar feedback. Tente novamente.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setSubmitStatus(null);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content feedback-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>
            <MessageSquare size={20} />
            Enviar Feedback
          </h3>
          <button className="modal-close" onClick={handleClose}>
            <X size={20} />
          </button>
        </div>

        <div className="modal-body">
          {submitStatus ? (
            <div className={`feedback-result ${submitStatus.success ? 'success' : 'error'}`}>
              <div className="result-icon">
                {submitStatus.success ? (
                  <CheckCircle size={48} />
                ) : (
                  <X size={48} />
                )}
              </div>
              <h4>{submitStatus.success ? 'Feedback Enviado!' : 'Erro'}</h4>
              <p>{submitStatus.message}</p>
              {submitStatus.issueUrl && (
                <a
                  href={submitStatus.issueUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="issue-link"
                >
                  Ver Issue no GitHub
                </a>
              )}
              <button className="btn-secondary" onClick={handleClose}>
                Fechar
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="feedback-form">
              <div className="form-group">
                <label htmlFor="feedback-type">Tipo de Feedback *</label>
                <select
                  id="feedback-type"
                  name="type"
                  value={formData.type}
                  onChange={handleInputChange}
                  required
                >
                  <option value="suggestion">Sugestão</option>
                  <option value="bug">Bug/Erro</option>
                  <option value="feature">Nova Funcionalidade</option>
                  <option value="other">Outro</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="feedback-title">Título *</label>
                <input
                  type="text"
                  id="feedback-title"
                  name="title"
                  value={formData.title}
                  onChange={handleInputChange}
                  placeholder="Resuma seu feedback em poucas palavras"
                  required
                  maxLength={100}
                />
              </div>

              <div className="form-group">
                <label htmlFor="feedback-description">Descrição *</label>
                <textarea
                  id="feedback-description"
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  placeholder="Descreva detalhadamente seu feedback, sugestões ou problema encontrado"
                  required
                  rows={4}
                  maxLength={1000}
                />
              </div>

              <div className="form-group">
                <label htmlFor="feedback-email">Email (opcional)</label>
                <input
                  type="email"
                  id="feedback-email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  placeholder="seu.email@exemplo.com"
                />
                <small className="form-hint">
                  Opcional: para que possamos entrar em contato se necessário
                </small>
              </div>

              <div className="form-group">
                <label htmlFor="feedback-context">Contexto Adicional (opcional)</label>
                <textarea
                  id="feedback-context"
                  name="context"
                  value={formData.context}
                  onChange={handleInputChange}
                  placeholder="Ex: nome do relatório, arquivo CSV, página onde ocorreu o problema..."
                  rows={2}
                  maxLength={500}
                />
              </div>

              <div className="form-actions">
                <button type="button" className="btn-secondary" onClick={handleClose}>
                  Cancelar
                </button>
                <button type="submit" disabled={isSubmitting} className="btn-primary">
                  {isSubmitting ? (
                    <>
                      <Loader2 className="animate-spin" />
                      Enviando...
                    </>
                  ) : (
                    "Enviar Feedback"
                  )}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default FeedbackModal;
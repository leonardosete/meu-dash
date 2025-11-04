import React, { useState } from "react";
import FileInput from "./FileInput";
import {
  uploadStandardAnalysis,
  uploadComparativeAnalysis,
} from "../services/api";
import { Loader2, LogIn } from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { UploadSuccessResponse } from "../types";
import InlineLoginForm from "./InlineLoginForm";

interface UploadFormsProps {
  onUploadSuccess: (data: UploadSuccessResponse) => void;
}

const UploadForms: React.FC<UploadFormsProps> = ({ onUploadSuccess }) => {
  const { isAuthenticated } = useAuth();
  const [padraoFile, setPadraoFile] = useState<FileList | null>(null);
  const [fileAntigo, setFileAntigo] = useState<FileList | null>(null);
  const [fileRecente, setFileRecente] = useState<FileList | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [standardError, setStandardError] = useState<string | null>(null);
  const [comparativeError, setComparativeError] = useState<string | null>(null);
  const [showLoginForm, setShowLoginForm] = useState(false);

  const handlePadraoSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!padraoFile || padraoFile.length === 0) {
      alert("Por favor, selecione um arquivo.");
      return;
    }
    setIsLoading(true);
    setStandardError(null);
    try {
      const result = await uploadStandardAnalysis(padraoFile[0]);
      onUploadSuccess(result);
    } catch (err) {
      const apiError = err as { response?: { data?: { error?: string } } };
      setStandardError(
        apiError.response?.data?.error || "Ocorreu um erro no upload.",
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleComparativaSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fileAntigo || fileAntigo.length === 0) {
      setComparativeError("Por favor, selecione o arquivo antigo.");
      return;
    }
    if (!fileRecente || fileRecente.length === 0) {
      setComparativeError("Por favor, selecione o arquivo recente.");
      return;
    }
    setIsLoading(true);
    setComparativeError(null);
    try {
      const result = await uploadComparativeAnalysis(
        fileAntigo[0],
        fileRecente[0],
      );
      if (result.report_url) {
        window.location.href = result.report_url;
      }
    } catch (err) {
      const apiError = err as { response?: { data?: { error?: string } } };
      setComparativeError(
        apiError.response?.data?.error || "Ocorreu um erro na comparação.",
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="form-section">
      <div className="upload-forms-container" style={{ position: "relative" }}>
        {!isAuthenticated && (
          <div className="form-disabled-overlay">
            {showLoginForm ? (
              <InlineLoginForm />
            ) : (
              <div
                className="overlay-content"
                onClick={() => setShowLoginForm(true)}
              >
                <LogIn size={20} />
                <span>Faça login para habilitar a análise</span>
              </div>
            )}
          </div>
        )}
        <div className={!isAuthenticated ? "forms-wrapper-disabled" : ""}>
          <div className="upload-forms-grid">
            {/* --- Bloco de Análise Padrão --- */}
            <div className="upload-form-card">
              <h3>Análise Padrão</h3>
              <p className="form-description">
                Faça upload do arquivo CSV mais recente para gerar relatório automático comparado com a última análise do histórico.
              </p>
              <form onSubmit={handlePadraoSubmit}>
                {standardError && (
                  <div className="error-message">{standardError}</div>
                )}
                <div style={{ marginBottom: "15px" }}>
                  <FileInput
                    id="file_recente"
                    name="file_recente"
                    onFileChange={setPadraoFile}
                    isMultiple={false}
                  />
                </div>
                <button type="submit" disabled={isLoading}>
                  {isLoading ? (
                    <Loader2 className="animate-spin" />
                  ) : (
                    "Analisar"
                  )}
                </button>
              </form>
            </div>

            {/* --- Bloco de Análise Comparativa --- */}
            <div className="upload-form-card">
              <h3>Análise Comparativa</h3>
              <p className="form-description">
                Compare dois arquivos CSV específicos para análise de tendência entre períodos selecionados.
              </p>
              <form onSubmit={handleComparativaSubmit}>
                {comparativeError && (
                  <div className="error-message">{comparativeError}</div>
                )}
                <div style={{ marginBottom: "15px" }}>
                  <FileInput
                    id="file_antigo"
                    name="file_antigo"
                    onFileChange={setFileAntigo}
                    isMultiple={false}
                  />
                </div>
                <div style={{ marginBottom: "15px", marginTop: "15px" }}>
                  <FileInput
                    id="file_recente_comp"
                    name="file_recente_comp"
                    onFileChange={setFileRecente}
                    isMultiple={false}
                  />
                </div>
                <button type="submit" disabled={isLoading}>
                  {isLoading ? (
                    <Loader2 className="animate-spin" />
                  ) : (
                    "Analisar"
                  )}
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UploadForms;
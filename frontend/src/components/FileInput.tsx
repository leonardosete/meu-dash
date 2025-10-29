import React, { useState, useRef, DragEvent } from "react";

interface FileInputProps {
  id: string;
  name: string;
  isMultiple?: boolean;
  onFileChange: (files: FileList | null) => void;
}

const FileInput: React.FC<FileInputProps> = ({
  id,
  name,
  isMultiple = false,
  onFileChange,
}) => {
  const [fileName, setFileName] = useState("");
  const [isDragActive, setIsDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    updateFileName(files);
    onFileChange(files);
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragActive(false);
    const files = event.dataTransfer.files;
    if (inputRef.current) {
      inputRef.current.files = files;
    }
    updateFileName(files);
    onFileChange(files);
  };

  const updateFileName = (files: FileList | null) => {
    if (files && files.length > 0) {
      setFileName(
        isMultiple
          ? `${files.length} arquivo(s) selecionado(s)`
          : files[0].name,
      );
    } else {
      setFileName("");
    }
  };

  return (
    <div
      className={`file-input-wrapper ${isDragActive ? "drag-active" : ""}`}
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragActive(true);
      }}
      onDragLeave={() => setIsDragActive(false)}
      onDrop={handleDrop}
    >
      <input
        type="file"
        id={id}
        name={name}
        multiple={isMultiple}
        ref={inputRef}
        onChange={handleFileChange}
        className="file-input"
      />
      {fileName ? (
        <span className="file-name">{fileName}</span>
      ) : (
        <span className="file-input-text">
          Clique ou arraste o arquivo aqui
        </span>
      )}
    </div>
  );
};

export default FileInput;

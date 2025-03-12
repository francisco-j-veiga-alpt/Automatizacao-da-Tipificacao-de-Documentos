// src/components/FileUploader.tsx
import React, { useState } from 'react';
import { uploadFileToApi } from '../services/api';

interface FileUploaderProps {
  onUploadComplete?: () => void; // Optional callback for when upload completes
}

const FileUploader: React.FC<FileUploaderProps> = ({ onUploadComplete }) => {
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState<string>("");

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      setFile(event.target.files[0]);
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!file) return;

    try {
      await uploadFileToApi(file);
      setMessage("File uploaded successfully!");
      if (onUploadComplete) onUploadComplete();
    } catch (error) {
      console.error(error);
      setMessage("Failed to upload file.");
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input type="file" accept=".csv" onChange={handleChange} />
      <button type="submit">Upload</button>
      {message && <p>{message}</p>}
    </form>
  );
};

export default FileUploader;

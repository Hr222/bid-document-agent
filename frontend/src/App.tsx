import { FormEvent, useMemo, useState } from "react";

import { ingestUpload, previewUpload } from "./api/policyPipeline";
import { ResultPanel } from "./components/ResultPanel";
import { UploadForm } from "./components/UploadForm";
import { UI_TEXT } from "./constants/uiText";
import type { PipelineResponse, PreviewUploadResponse } from "./types/pipeline";

export default function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [policyCategory, setPolicyCategory] = useState<string>(UI_TEXT.defaultCategory);
  const [responsibleDepartment, setResponsibleDepartment] = useState<string>(
    UI_TEXT.defaultDepartment,
  );
  const [versionLabel, setVersionLabel] = useState("");
  const [previewResult, setPreviewResult] = useState<PreviewUploadResponse | null>(null);
  const [ingestResult, setIngestResult] = useState<PipelineResponse | null>(null);
  const [loadingAction, setLoadingAction] = useState<"preview" | "ingest" | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const canPreview = Boolean(selectedFile) && loadingAction === null;
  const canIngest = Boolean(previewResult?.upload_id) && loadingAction === null;

  const currentResult = useMemo(
    () => ingestResult ?? previewResult,
    [ingestResult, previewResult],
  );

  function handleFileSelect(file: File | null) {
    setSelectedFile(file);
    setPreviewResult(null);
    setIngestResult(null);
    setErrorMessage(null);
  }

  async function handlePreview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!selectedFile) {
      setErrorMessage(UI_TEXT.chooseFileFirst);
      return;
    }

    setLoadingAction("preview");
    setErrorMessage(null);
    setPreviewResult(null);
    setIngestResult(null);

    try {
      const payload = await previewUpload({
        file: selectedFile,
        policyCategory,
        responsibleDepartment,
        versionLabel,
      });
      setPreviewResult(payload);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : UI_TEXT.previewFailed);
    } finally {
      setLoadingAction(null);
    }
  }

  async function handleIngest() {
    if (!previewResult?.upload_id) {
      setErrorMessage(UI_TEXT.previewFirst);
      return;
    }

    setLoadingAction("ingest");
    setErrorMessage(null);
    setIngestResult(null);

    try {
      const payload = await ingestUpload({
        uploadId: previewResult.upload_id,
        policyCategory,
        responsibleDepartment,
        versionLabel,
      });
      setIngestResult(payload);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : UI_TEXT.ingestFailed);
    } finally {
      setLoadingAction(null);
    }
  }

  return (
    <main className="page-shell">
      <section className="page-header">
        <p className="eyebrow">{UI_TEXT.appEyebrow}</p>
        <h1>{UI_TEXT.appTitle}</h1>
        <p className="lede">{UI_TEXT.appIntro}</p>
      </section>

      <section className="workspace">
        <UploadForm
          selectedFile={selectedFile}
          policyCategory={policyCategory}
          responsibleDepartment={responsibleDepartment}
          versionLabel={versionLabel}
          loadingAction={loadingAction}
          canPreview={canPreview}
          canIngest={canIngest}
          errorMessage={errorMessage}
          onFileSelect={handleFileSelect}
          onPolicyCategoryChange={setPolicyCategory}
          onResponsibleDepartmentChange={setResponsibleDepartment}
          onVersionLabelChange={setVersionLabel}
          onPreview={handlePreview}
          onIngest={handleIngest}
        />

        <ResultPanel result={currentResult} />
      </section>
    </main>
  );
}

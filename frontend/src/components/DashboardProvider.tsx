import React, { useState, useCallback, ReactNode } from "react";
import { ReportUrls } from "../types";
import { DashboardContext } from "../contexts/DashboardContext";

export const DashboardProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const [reportUrls, setReportUrls] = useState<ReportUrls | null>(null);
  const [quickDiagnosis, setQuickDiagnosis] = useState<string | null>(null);

  const handleSetReportUrls = useCallback((urls: ReportUrls | null) => {
    setReportUrls(urls);
    if (urls === null) {
      setQuickDiagnosis(null);
    }
  }, []);

  const handleSetQuickDiagnosis = useCallback((html: string | null) => {
    setQuickDiagnosis(html);
  }, []);

  const value = {
    reportUrls,
    setReportUrls: handleSetReportUrls,
    quickDiagnosis,
    setQuickDiagnosis: handleSetQuickDiagnosis,
  };

  return (
    <DashboardContext.Provider value={value}>
      {children}
    </DashboardContext.Provider>
  );
};

export default DashboardProvider;
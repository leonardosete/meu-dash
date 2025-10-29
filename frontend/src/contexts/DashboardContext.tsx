import { createContext } from "react";
import { ReportUrls } from "../types";

interface DashboardContextType {
  reportUrls: ReportUrls | null;
  setReportUrls: (urls: ReportUrls | null) => void;
  quickDiagnosis: string | null;
  setQuickDiagnosis: (html: string | null) => void;
}

export const DashboardContext = createContext<DashboardContextType | undefined>(
  undefined,
);
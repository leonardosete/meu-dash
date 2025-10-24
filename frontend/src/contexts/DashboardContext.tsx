import React, { createContext, useState, useCallback, ReactNode, useContext } from 'react';
import { ReportUrls } from '../types';

interface DashboardContextType {
  reportUrls: ReportUrls | null;
  setReportUrls: (urls: ReportUrls | null) => void;
}

export const DashboardContext = createContext<DashboardContextType | undefined>(undefined);

export const DashboardProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [reportUrls, setReportUrls] = useState<ReportUrls | null>(null);

  const handleSetReportUrls = useCallback((urls: ReportUrls | null) => {
    setReportUrls(urls);
  }, []);

  const value = { reportUrls, setReportUrls: handleSetReportUrls };

  return <DashboardContext.Provider value={value}>{children}</DashboardContext.Provider>;
};

export const useDashboard = () => {
  const context = useContext(DashboardContext);
  if (context === undefined) {
    throw new Error('useDashboard must be used within a DashboardProvider');
  }
  return context;
};
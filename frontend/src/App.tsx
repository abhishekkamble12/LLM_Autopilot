import React, { useState } from 'react';
import { Navbar } from './components/Navbar';
import { Playground } from './components/Playground';
import { Dashboard } from './components/Dashboard';
import { ChatResponse, SystemStats } from './types';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'playground' | 'dashboard'>('playground');
  const [stats, setStats] = useState<SystemStats>({
    totalRequests: 0,
    totalCostSaved: 0,
    totalCostSpent: 0,
    cacheHitCount: 0,
    averageLatencyMs: 0
  });

  const handleMessageSent = (res: ChatResponse) => {
    setStats(prev => ({
      totalRequests: prev.totalRequests + 1,
      totalCostSaved: prev.totalCostSaved + res.savings,
      totalCostSpent: prev.totalCostSpent + res.cost,
      cacheHitCount: res.complexity_label === 'CACHED' ? prev.cacheHitCount + 1 : prev.cacheHitCount,
      averageLatencyMs: prev.averageLatencyMs
    }));
  };

  return (
    <div className="app-container">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />
      <main className="main-content">
        {activeTab === 'playground' ? (
          <Playground onMessageSent={handleMessageSent} />
        ) : (
          <Dashboard stats={stats} />
        )}
      </main>
    </div>
  );
};

export default App;

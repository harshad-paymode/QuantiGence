import { useQuery } from '@tanstack/react-query';
import { useDashboardStore } from '@/store/useDashboardStore';

export const useChartData = () => {
  const { quantCompany, quantPeriod, quantVariable } = useDashboardStore();

  return useQuery({
    queryKey: ['chartData', quantCompany, quantPeriod, quantVariable],
    queryFn: async () => {
      const res = await fetch(`http://localhost:8000/api/chart?company=${quantCompany}&period=${quantPeriod}&variable=${quantVariable}`);
      if (!res.ok) throw new Error('Network response was not ok');
      return res.json();
    }
  });
};
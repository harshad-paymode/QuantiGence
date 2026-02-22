'use client';
import dynamic from 'next/dynamic';

// Dynamically import to prevent SSR issues
const Chart = dynamic(() => import('react-apexcharts'), { ssr: false });

interface ChartProps {
  data: any[];
  variables: string[];
}

export default function QuantitativeChart({ data, variables }: ChartProps) {
  // 1. Identify if we have the specific "Big Four" for a candle chart
  // We use lowercase for the check to be safe, but map to the actual keys
  const lowerVars = variables.map(v => v.toLowerCase());
  const hasOHLC = ['open', 'high', 'low', 'close'].every(v => lowerVars.includes(v));

  // 2. Determine Chart Type and Data Structure
  // Candlestick only triggers if EXACTLY the 4 OHLC variables are selected
  const isCandleView = hasOHLC && variables.length === 4;
  const chartType = isCandleView ? 'candlestick' : 'line';

  let series: any[] = [];

  if (isCandleView) {
    // CANDLESTICK STRUCTURE: One series, y is [O, H, L, C]
    series = [{
      name: 'Price',
      data: data.map(item => ({
        x: new Date(item.date).getTime(),
        y: [
          Number(item.Open), 
          Number(item.High), 
          Number(item.Low), 
          Number(item.Close)
        ]
      }))
    }];
  } else {
    // LINE STRUCTURE: Multiple series, y is a single number
    series = variables.map(v => ({
      name: v,
      data: data.map(item => ({
        x: new Date(item.date).getTime(),
        y: Number(item[v])
      }))
    }));
  }

  // 3. Configuration
  const options: any = {
    chart: {
      type: chartType,
      background: 'transparent',
      toolbar: { show: true },
      animations: { enabled: false } // Faster for financial data
    },
    theme: { mode: 'dark' },
    stroke: {
      // Candlesticks shouldn't have "smooth" curves
      curve: isCandleView ? 'straight' : 'smooth',
      width: isCandleView ? 1 : (variables.length === 1 ? 3 : 2)
    },
    xaxis: {
      type: 'datetime',
      labels: { style: { colors: '#94a3b8' } }
    },
    yaxis: {
      labels: { 
        style: { colors: '#94a3b8' },
        formatter: (val: number) => val?.toFixed(2)
      }
    },
    grid: { borderColor: '#1e293b' },
    tooltip: { theme: 'dark' },
    // Specific colors for Candlesticks (Green for up, Red for down)
    plotOptions: {
      candlestick: {
        colors: {
          positive: '#10b981',
          negative: '#ef4444'
        }
      }
    }
  };

  return (
    <div className="w-full h-full min-h-0">
      <Chart
        options={options}
        series={series}
        type={chartType}
        height={'100%'}
        width="100%"
        />
    </div>
  );
}
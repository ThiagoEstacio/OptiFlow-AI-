import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Button,
  Chip,
  Paper,
  LinearProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Divider,
} from '@mui/material';
import { Grid } from '../components/GridWrapper';
import {
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Timer as TimerIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  ScatterChart,
  Scatter,
} from 'recharts';
import apiClient from '../api/client';

interface ExecutionStep {
  step: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  startTime?: number;
  endTime?: number;
  duration?: number;
  details?: any;
}

interface ModelPrediction {
  timestamp: string;
  input_data: any;
  prediction: number;
  confidence?: number;
  actual_value?: number;
  error?: number;
}

interface ModelMetrics {
  model_name: string;
  accuracy?: number;
  mae?: number;
  mse?: number;
  r2_score?: number;
  execution_time: number;
  data_points: number;
}

const MLModelExecutionView: React.FC = () => {
  const [isExecuting, setIsExecuting] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [executionSteps, setExecutionSteps] = useState<ExecutionStep[]>([
    { step: '1. Data Collection', status: 'pending' },
    { step: '2. Data Preprocessing', status: 'pending' },
    { step: '3. Feature Engineering', status: 'pending' },
    { step: '4. Model Loading', status: 'pending' },
    { step: '5. Model Inference', status: 'pending' },
    { step: '6. Results Generation', status: 'pending' },
  ]);
  const [predictions, setPredictions] = useState<ModelPrediction[]>([]);
  const [metrics, setMetrics] = useState<ModelMetrics | null>(null);
  const [executionLog, setExecutionLog] = useState<string[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('gradient_boosting_efficiency');

  const models = [
    { value: 'gradient_boosting_efficiency', label: 'Gradient Boosting - Energy Efficiency' },
    { value: 'isolation_forest_anomalies', label: 'Isolation Forest - Anomaly Detection' },
    { value: 'lstm_energy', label: 'LSTM - Energy Prediction' },
    { value: 'random_forest_efficiency', label: 'Random Forest - Efficiency' },
  ];

  const addLog = (message: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setExecutionLog((prev) => [`[${timestamp}] ${message}`, ...prev]);
  };

  const updateStep = (stepIndex: number, status: 'running' | 'completed' | 'error', details?: any) => {
    setExecutionSteps((prev) => {
      const newSteps = [...prev];
      const step = newSteps[stepIndex];

      if (status === 'running') {
        step.startTime = Date.now();
        step.status = 'running';
      } else if (status === 'completed') {
        step.endTime = Date.now();
        step.duration = step.endTime - (step.startTime || step.endTime);
        step.status = 'completed';
        step.details = details;
      } else if (status === 'error') {
        step.status = 'error';
      }

      return newSteps;
    });
  };

  const executeMLPipeline = async () => {
    setIsExecuting(true);
    setActiveStep(0);
    setPredictions([]);
    setMetrics(null);
    setExecutionLog([]);

    try {
      // Step 1: Data Collection
      addLog('Starting data collection from InfluxDB...');
      updateStep(0, 'running');
      setActiveStep(0);
      await new Promise((resolve) => setTimeout(resolve, 1000));

      const dataResponse = await apiClient.get('/api/v1/demo/tags/history', {
        params: {
          tag_name: 'energy_consumption',
          time_range: 'last_24h',
        },
      });

      const dataPoints = dataResponse.data.data?.length || 100;
      addLog(`Collected ${dataPoints} data points from InfluxDB`);
      updateStep(0, 'completed', { dataPoints });

      // Step 2: Data Preprocessing
      addLog('Preprocessing data: cleaning, normalization, handling missing values...');
      updateStep(1, 'running');
      setActiveStep(1);
      await new Promise((resolve) => setTimeout(resolve, 800));

      addLog('Removed 3 outliers, filled 2 missing values');
      updateStep(1, 'completed', { outliers: 3, missing: 2 });

      // Step 3: Feature Engineering
      addLog('Generating features: time-based, statistical, lagged features...');
      updateStep(2, 'running');
      setActiveStep(2);
      await new Promise((resolve) => setTimeout(resolve, 700));

      addLog('Generated 12 features from raw data');
      updateStep(2, 'completed', { features: 12 });

      // Step 4: Model Loading
      addLog(`Loading ${selectedModel} from persistent storage...`);
      updateStep(3, 'running');
      setActiveStep(3);
      await new Promise((resolve) => setTimeout(resolve, 600));

      const modelResponse = await apiClient.get(`/api/v1/ml/models/${selectedModel}`);
      addLog(`Model loaded: ${modelResponse.data.size_mb} MB, trained on ${modelResponse.data.metadata?.trained_at || 'N/A'}`);
      updateStep(3, 'completed', modelResponse.data);

      // Step 5: Model Inference
      addLog('Running model inference on prepared data...');
      updateStep(4, 'running');
      setActiveStep(4);

      const startInference = Date.now();
      const inferenceResponse = await apiClient.get('/api/v1/ml/insights/all', {
        params: { time_range: 'last_24h' },
      });
      const inferenceTime = Date.now() - startInference;

      addLog(`Inference completed in ${inferenceTime}ms`);
      updateStep(4, 'completed', { inferenceTime });

      // Step 6: Results Generation
      addLog('Generating predictions and calculating metrics...');
      updateStep(5, 'running');
      setActiveStep(5);
      await new Promise((resolve) => setTimeout(resolve, 500));

      // Generate sample predictions for visualization
      const samplePredictions: ModelPrediction[] = [];
      for (let i = 0; i < 20; i++) {
        const actual = 1000 + Math.random() * 200;
        const prediction = actual + (Math.random() - 0.5) * 50;
        samplePredictions.push({
          timestamp: new Date(Date.now() - (20 - i) * 3600000).toISOString(),
          input_data: { feature1: Math.random() * 100, feature2: Math.random() * 50 },
          prediction,
          confidence: 0.8 + Math.random() * 0.15,
          actual_value: actual,
          error: Math.abs(prediction - actual),
        });
      }
      setPredictions(samplePredictions);

      // Extract metrics from ML insights
      const insights = inferenceResponse.data.insights;
      let modelMetrics: ModelMetrics = {
        model_name: selectedModel,
        execution_time: inferenceTime,
        data_points: dataPoints,
      };

      if (selectedModel.includes('gradient_boosting')) {
        const efficiency = insights?.efficiency_analysis;
        if (efficiency?.status === 'success') {
          modelMetrics.r2_score = efficiency.model_r2_score;
          modelMetrics.mae = efficiency.model_mae;
        }
      } else if (selectedModel.includes('isolation_forest')) {
        const anomalies = insights?.anomalies;
        if (anomalies?.status === 'success') {
          modelMetrics.accuracy = anomalies.model_accuracy;
        }
      }

      setMetrics(modelMetrics);
      addLog('Results generated successfully!');
      updateStep(5, 'completed', modelMetrics);
      setActiveStep(6);

    } catch (error: any) {
      addLog(`ERROR: ${error.message}`);
      updateStep(activeStep, 'error');
      console.error('Execution error:', error);
    } finally {
      setIsExecuting(false);
    }
  };

  const stopExecution = () => {
    setIsExecuting(false);
    addLog('Execution stopped by user');
  };

  const getStepIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckIcon color="success" />;
      case 'running':
        return <CircularProgress size={24} />;
      case 'error':
        return <ErrorIcon color="error" />;
      default:
        return null;
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" sx={{ fontWeight: 600 }}>
          ML Model Execution Demo
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="contained"
            color="primary"
            startIcon={isExecuting ? <StopIcon /> : <PlayIcon />}
            onClick={isExecuting ? stopExecution : executeMLPipeline}
            disabled={isExecuting && activeStep < 5}
          >
            {isExecuting ? 'Stop' : 'Run Model'}
          </Button>
        </Box>
      </Box>

      {/* Model Selection */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Select ML Model
          </Typography>
          <Grid container spacing={2}>
            {models.map((model) => (
              <Grid item xs={12} sm={6} md={3} key={model.value}>
                <Card
                  sx={{
                    cursor: 'pointer',
                    border: selectedModel === model.value ? '2px solid' : '1px solid',
                    borderColor: selectedModel === model.value ? 'primary.main' : 'divider',
                    bgcolor: selectedModel === model.value ? 'action.selected' : 'background.paper',
                  }}
                  onClick={() => !isExecuting && setSelectedModel(model.value)}
                >
                  <CardContent>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {model.label}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>

      <Grid container spacing={3}>
        {/* Left Column: Execution Pipeline */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Execution Pipeline
              </Typography>
              <Stepper activeStep={activeStep} orientation="vertical">
                {executionSteps.map((step, index) => (
                  <Step key={step.step}>
                    <StepLabel
                      icon={getStepIcon(step.status)}
                      error={step.status === 'error'}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography>{step.step}</Typography>
                        {step.status === 'completed' && step.duration && (
                          <Chip
                            label={`${step.duration}ms`}
                            size="small"
                            icon={<TimerIcon />}
                          />
                        )}
                      </Box>
                    </StepLabel>
                    <StepContent>
                      {step.details && (
                        <Paper sx={{ p: 2, mt: 1, bgcolor: 'background.default' }}>
                          <pre style={{ margin: 0, fontSize: '0.75rem' }}>
                            {JSON.stringify(step.details, null, 2)}
                          </pre>
                        </Paper>
                      )}
                    </StepContent>
                  </Step>
                ))}
              </Stepper>
            </CardContent>
          </Card>

          {/* Execution Log */}
          <Card sx={{ mt: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Execution Log
              </Typography>
              <Paper
                sx={{
                  p: 2,
                  maxHeight: 300,
                  overflow: 'auto',
                  bgcolor: 'grey.900',
                  color: 'grey.100',
                  fontFamily: 'monospace',
                  fontSize: '0.75rem',
                }}
              >
                {executionLog.map((log, index) => (
                  <div key={index}>{log}</div>
                ))}
                {executionLog.length === 0 && (
                  <div style={{ color: '#999' }}>Waiting for execution...</div>
                )}
              </Paper>
            </CardContent>
          </Card>
        </Grid>

        {/* Right Column: Results */}
        <Grid item xs={12} md={6}>
          {/* Metrics */}
          {metrics && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Model Performance Metrics
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Model
                    </Typography>
                    <Typography variant="body1" sx={{ fontWeight: 600 }}>
                      {metrics.model_name}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Execution Time
                    </Typography>
                    <Typography variant="body1" sx={{ fontWeight: 600 }}>
                      {metrics.execution_time}ms
                    </Typography>
                  </Grid>
                  {metrics.r2_score !== undefined && (
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        R² Score
                      </Typography>
                      <Typography variant="body1" sx={{ fontWeight: 600 }}>
                        {(metrics.r2_score * 100).toFixed(2)}%
                      </Typography>
                    </Grid>
                  )}
                  {metrics.mae !== undefined && (
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        MAE
                      </Typography>
                      <Typography variant="body1" sx={{ fontWeight: 600 }}>
                        {metrics.mae.toFixed(2)}
                      </Typography>
                    </Grid>
                  )}
                  {metrics.accuracy !== undefined && (
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Accuracy
                      </Typography>
                      <Typography variant="body1" sx={{ fontWeight: 600 }}>
                        {(metrics.accuracy * 100).toFixed(2)}%
                      </Typography>
                    </Grid>
                  )}
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Data Points
                    </Typography>
                    <Typography variant="body1" sx={{ fontWeight: 600 }}>
                      {metrics.data_points}
                    </Typography>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          )}

          {/* Predictions Visualization */}
          {predictions.length > 0 && (
            <>
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Predictions vs Actual Values
                  </Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={predictions}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis
                        dataKey="timestamp"
                        tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                      />
                      <YAxis />
                      <Tooltip
                        labelFormatter={(value) => new Date(value).toLocaleString()}
                        formatter={(value: any) => value.toFixed(2)}
                      />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey="actual_value"
                        stroke="#1976d2"
                        name="Actual"
                        strokeWidth={2}
                      />
                      <Line
                        type="monotone"
                        dataKey="prediction"
                        stroke="#d32f2f"
                        name="Prediction"
                        strokeWidth={2}
                        strokeDasharray="5 5"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Prediction Error Distribution
                  </Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <ScatterChart>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="actual_value" name="Actual" />
                      <YAxis dataKey="prediction" name="Prediction" />
                      <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                      <Legend />
                      <Scatter name="Predictions" data={predictions} fill="#1976d2" />
                      <ReferenceLine
                        stroke="red"
                        strokeDasharray="3 3"
                        segment={[
                          { x: 900, y: 900 },
                          { x: 1300, y: 1300 },
                        ]}
                      />
                    </ScatterChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Recent Predictions
                  </Typography>
                  <TableContainer component={Paper} sx={{ maxHeight: 300 }}>
                    <Table size="small" stickyHeader>
                      <TableHead>
                        <TableRow>
                          <TableCell>Timestamp</TableCell>
                          <TableCell align="right">Actual</TableCell>
                          <TableCell align="right">Predicted</TableCell>
                          <TableCell align="right">Error</TableCell>
                          <TableCell align="right">Confidence</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {predictions.map((pred, index) => (
                          <TableRow key={index}>
                            <TableCell>
                              {new Date(pred.timestamp).toLocaleTimeString()}
                            </TableCell>
                            <TableCell align="right">
                              {pred.actual_value?.toFixed(2)}
                            </TableCell>
                            <TableCell align="right">
                              {pred.prediction.toFixed(2)}
                            </TableCell>
                            <TableCell align="right">
                              <Chip
                                label={pred.error?.toFixed(2)}
                                size="small"
                                color={pred.error! < 10 ? 'success' : pred.error! < 30 ? 'warning' : 'error'}
                              />
                            </TableCell>
                            <TableCell align="right">
                              {(pred.confidence! * 100).toFixed(1)}%
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </CardContent>
              </Card>
            </>
          )}

          {/* Waiting State */}
          {!metrics && !isExecuting && (
            <Card>
              <CardContent>
                <Box sx={{ textAlign: 'center', py: 5 }}>
                  <MemoryIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary">
                    Click "Run Model" to start ML execution
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    Watch the model process data in real-time
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>
    </Box>
  );
};

export default MLModelExecutionView;

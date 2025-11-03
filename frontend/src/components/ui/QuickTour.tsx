import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  IconButton,
  Stepper,
  Step,
  StepLabel,
  Dialog,
  DialogContent,
  LinearProgress,
} from '@mui/material';
import { Close as CloseIcon, NavigateBefore, NavigateNext, CheckCircle } from '@mui/icons-material';

interface TourStep {
  title: string;
  description: string;
  image?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

interface QuickTourProps {
  steps: TourStep[];
  open: boolean;
  onClose: () => void;
  onComplete?: () => void;
}

export const QuickTour: React.FC<QuickTourProps> = ({ steps, open, onClose, onComplete }) => {
  const [activeStep, setActiveStep] = useState(0);

  const handleNext = () => {
    if (activeStep === steps.length - 1) {
      onComplete?.();
      onClose();
    } else {
      setActiveStep((prev) => prev + 1);
    }
  };

  const handleBack = () => {
    setActiveStep((prev) => prev - 1);
  };

  const currentStep = steps[activeStep];
  const progress = ((activeStep + 1) / steps.length) * 100;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogContent sx={{ p: 0, position: 'relative' }}>
        <IconButton
          onClick={onClose}
          sx={{
            position: 'absolute',
            right: 8,
            top: 8,
            zIndex: 1,
            bgcolor: 'background.paper',
            '&:hover': { bgcolor: 'grey.100' },
          }}
        >
          <CloseIcon />
        </IconButton>

        {/* Progress Bar */}
        <LinearProgress variant="determinate" value={progress} sx={{ height: 4 }} />

        <Box sx={{ p: 4 }}>
          {/* Step Content */}
          <Box sx={{ mb: 4, minHeight: 250 }}>
            {currentStep.image && (
              <Box
                component="img"
                src={currentStep.image}
                alt={currentStep.title}
                sx={{
                  width: '100%',
                  maxHeight: 200,
                  objectFit: 'cover',
                  borderRadius: 2,
                  mb: 3,
                }}
              />
            )}

            <Typography variant="h5" gutterBottom fontWeight="bold">
              {currentStep.title}
            </Typography>

            <Typography variant="body1" color="text.secondary" paragraph>
              {currentStep.description}
            </Typography>

            {currentStep.action && (
              <Button
                variant="outlined"
                onClick={currentStep.action.onClick}
                sx={{ mt: 2 }}
              >
                {currentStep.action.label}
              </Button>
            )}
          </Box>

          {/* Stepper */}
          <Stepper activeStep={activeStep} sx={{ mb: 3 }}>
            {steps.map((step, index) => (
              <Step key={index}>
                <StepLabel />
              </Step>
            ))}
          </Stepper>

          {/* Navigation */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Button
              onClick={handleBack}
              disabled={activeStep === 0}
              startIcon={<NavigateBefore />}
              variant="outlined"
            >
              Anterior
            </Button>

            <Typography variant="body2" color="text.secondary">
              Passo {activeStep + 1} de {steps.length}
            </Typography>

            <Button
              onClick={handleNext}
              variant="contained"
              endIcon={activeStep === steps.length - 1 ? <CheckCircle /> : <NavigateNext />}
            >
              {activeStep === steps.length - 1 ? 'Concluir' : 'Próximo'}
            </Button>
          </Box>
        </Box>
      </DialogContent>
    </Dialog>
  );
};

interface FeatureHighlightProps {
  title: string;
  description: string;
  badge?: string;
  image?: string;
  onDismiss: () => void;
  actionLabel?: string;
  onAction?: () => void;
}

export const FeatureHighlight: React.FC<FeatureHighlightProps> = ({
  title,
  description,
  badge,
  image,
  onDismiss,
  actionLabel,
  onAction,
}) => {
  return (
    <Paper
      sx={{
        position: 'fixed',
        bottom: 24,
        right: 24,
        maxWidth: 360,
        zIndex: 1300,
        boxShadow: 6,
        animation: 'slideIn 0.3s ease-out',
        '@keyframes slideIn': {
          from: {
            transform: 'translateY(100%)',
            opacity: 0,
          },
          to: {
            transform: 'translateY(0)',
            opacity: 1,
          },
        },
      }}
    >
      <Box sx={{ position: 'relative' }}>
        {badge && (
          <Box
            sx={{
              position: 'absolute',
              top: 12,
              right: 12,
              bgcolor: 'secondary.main',
              color: 'white',
              px: 1.5,
              py: 0.5,
              borderRadius: 10,
              fontSize: '0.75rem',
              fontWeight: 'bold',
            }}
          >
            {badge}
          </Box>
        )}

        <IconButton
          onClick={onDismiss}
          sx={{
            position: 'absolute',
            top: 8,
            left: 8,
            bgcolor: 'background.paper',
            '&:hover': { bgcolor: 'grey.100' },
          }}
          size="small"
        >
          <CloseIcon fontSize="small" />
        </IconButton>

        {image && (
          <Box
            component="img"
            src={image}
            alt={title}
            sx={{
              width: '100%',
              height: 150,
              objectFit: 'cover',
            }}
          />
        )}

        <Box sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom fontWeight="bold">
            {title}
          </Typography>

          <Typography variant="body2" color="text.secondary" paragraph>
            {description}
          </Typography>

          {actionLabel && onAction && (
            <Button variant="contained" onClick={onAction} fullWidth>
              {actionLabel}
            </Button>
          )}
        </Box>
      </Box>
    </Paper>
  );
};

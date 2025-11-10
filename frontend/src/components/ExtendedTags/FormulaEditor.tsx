/**
 * Formula Editor with Syntax Highlighting
 *
 * Advanced editor for mathematical formulas and logical conditions with:
 * - Syntax highlighting for tag references {TAG_NAME}
 * - Autocomplete for available tags
 * - Real-time validation
 * - Syntax hints
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  TextField,
  Paper,
  Chip,
  Typography,
  List,
  ListItem,
  ListItemText,
  Popper,
  ClickAwayListener,
  Alert
} from '@mui/material';
import { CheckCircle, Error as ErrorIcon } from '@mui/icons-material';

interface FormulaEditorProps {
  value: string;
  onChange: (value: string) => void;
  label?: string;
  placeholder?: string;
  helperText?: string;
  availableTags?: string[];
  mode?: 'formula' | 'condition';
  error?: string;
}

export const FormulaEditor: React.FC<FormulaEditorProps> = ({
  value,
  onChange,
  label = 'Fórmula',
  placeholder,
  helperText,
  availableTags = [],
  mode = 'formula',
  error
}) => {
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [cursorPosition, setCursorPosition] = useState(0);
  const [validationResult, setValidationResult] = useState<{
    valid: boolean;
    message?: string;
    tags?: string[];
  } | null>(null);

  const inputRef = useRef<HTMLTextAreaElement>(null);
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);

  // Extract tag references from formula
  const extractTagReferences = (formula: string): string[] => {
    const tagPattern = /\{([^}]+)\}/g;
    const matches = formula.matchAll(tagPattern);
    return Array.from(matches, m => m[1]);
  };

  // Validate formula syntax
  const validateFormula = (formula: string) => {
    if (!formula.trim()) {
      setValidationResult(null);
      return;
    }

    const referencedTags = extractTagReferences(formula);

    // Check for unmatched braces
    const openBraces = (formula.match(/\{/g) || []).length;
    const closeBraces = (formula.match(/\}/g) || []).length;

    if (openBraces !== closeBraces) {
      setValidationResult({
        valid: false,
        message: 'Chaves não balanceadas - verifique { }',
        tags: referencedTags
      });
      return;
    }

    // Check for invalid operators sequence
    const invalidSequence = /[+\-*/]{2,}/.test(formula.replace(/\{[^}]+\}/g, 'X'));
    if (invalidSequence) {
      setValidationResult({
        valid: false,
        message: 'Sequência inválida de operadores',
        tags: referencedTags
      });
      return;
    }

    setValidationResult({
      valid: true,
      message: `Fórmula válida - ${referencedTags.length} tag(s) referenciado(s)`,
      tags: referencedTags
    });
  };

  useEffect(() => {
    validateFormula(value);
  }, [value]);

  // Handle text change and show autocomplete
  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value;
    const cursorPos = e.target.selectionStart || 0;

    onChange(newValue);
    setCursorPosition(cursorPos);

    // Check if user is typing a tag reference
    const textBeforeCursor = newValue.substring(0, cursorPos);
    const lastOpenBrace = textBeforeCursor.lastIndexOf('{');
    const lastCloseBrace = textBeforeCursor.lastIndexOf('}');

    if (lastOpenBrace > lastCloseBrace && lastOpenBrace !== -1) {
      const searchTerm = textBeforeCursor.substring(lastOpenBrace + 1).toLowerCase();
      const filtered = availableTags.filter(tag =>
        tag.toLowerCase().includes(searchTerm)
      );

      if (filtered.length > 0) {
        setSuggestions(filtered);
        setShowSuggestions(true);
        setAnchorEl(e.target);
      } else {
        setShowSuggestions(false);
      }
    } else {
      setShowSuggestions(false);
    }
  };

  // Insert tag from autocomplete
  const insertTag = (tagName: string) => {
    const textBeforeCursor = value.substring(0, cursorPosition);
    const textAfterCursor = value.substring(cursorPosition);
    const lastOpenBrace = textBeforeCursor.lastIndexOf('{');

    const newValue =
      value.substring(0, lastOpenBrace + 1) +
      tagName +
      '}' +
      textAfterCursor;

    onChange(newValue);
    setShowSuggestions(false);

    // Set cursor after inserted tag
    setTimeout(() => {
      if (inputRef.current) {
        const newCursorPos = lastOpenBrace + tagName.length + 2;
        inputRef.current.setSelectionRange(newCursorPos, newCursorPos);
        inputRef.current.focus();
      }
    }, 0);
  };

  // Syntax highlighting for display
  const highlightSyntax = (text: string) => {
    if (!text) return null;

    const parts: React.ReactNode[] = [];
    let lastIndex = 0;
    const tagPattern = /\{([^}]+)\}/g;
    let match;

    while ((match = tagPattern.exec(text)) !== null) {
      // Add text before tag
      if (match.index > lastIndex) {
        parts.push(
          <span key={`text-${lastIndex}`} style={{ color: '#333' }}>
            {text.substring(lastIndex, match.index)}
          </span>
        );
      }

      // Add highlighted tag
      const tagName = match[1];
      const isValidTag = availableTags.includes(tagName);
      parts.push(
        <Chip
          key={`tag-${match.index}`}
          label={tagName}
          size="small"
          color={isValidTag ? 'primary' : 'error'}
          variant="outlined"
          sx={{
            mx: 0.5,
            height: 20,
            fontSize: '0.75rem',
            fontFamily: 'monospace'
          }}
        />
      );

      lastIndex = match.index + match[0].length;
    }

    // Add remaining text
    if (lastIndex < text.length) {
      parts.push(
        <span key={`text-${lastIndex}`} style={{ color: '#333' }}>
          {text.substring(lastIndex)}
        </span>
      );
    }

    return parts;
  };

  // Example formulas based on mode
  const examples = mode === 'formula' ? [
    '{TEMP_01} * 1.8 + 32',
    '({PRESSURE_A} + {PRESSURE_B}) / 2',
    '{FLOW_RATE} * {DENSITY} / 1000',
    'SQRT({POWER} / {RESISTANCE})'
  ] : [
    'if {TEMP} > 100 then 1 else 0',
    '{PRESSURE} >= {SET_POINT} and {STATUS} == 1',
    '{VALUE} between 10 and 50',
    'not {ALARM_ACTIVE}'
  ];

  return (
    <Box>
      <TextField
        fullWidth
        multiline
        rows={4}
        label={label}
        value={value}
        onChange={handleChange}
        placeholder={placeholder}
        helperText={helperText}
        error={!!error}
        inputRef={inputRef}
        InputProps={{
          sx: {
            fontFamily: 'monospace',
            fontSize: '0.9rem'
          }
        }}
      />

      {/* Syntax Preview */}
      {value && (
        <Paper
          variant="outlined"
          sx={{
            p: 2,
            mt: 1,
            backgroundColor: '#f5f5f5',
            minHeight: 60,
            fontFamily: 'monospace',
            fontSize: '0.9rem'
          }}
        >
          <Typography variant="caption" color="text.secondary" gutterBottom>
            Preview com Syntax Highlighting:
          </Typography>
          <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 0.5 }}>
            {highlightSyntax(value)}
          </Box>
        </Paper>
      )}

      {/* Validation Result */}
      {validationResult && (
        <Alert
          severity={validationResult.valid ? 'success' : 'error'}
          icon={validationResult.valid ? <CheckCircle /> : <ErrorIcon />}
          sx={{ mt: 1 }}
        >
          <Typography variant="body2">
            {validationResult.message}
          </Typography>
          {validationResult.tags && validationResult.tags.length > 0 && (
            <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {validationResult.tags.map((tag, idx) => (
                <Chip
                  key={idx}
                  label={tag}
                  size="small"
                  color={availableTags.includes(tag) ? 'success' : 'warning'}
                  variant="outlined"
                />
              ))}
            </Box>
          )}
        </Alert>
      )}

      {/* Autocomplete Suggestions */}
      <Popper
        open={showSuggestions}
        anchorEl={anchorEl}
        placement="bottom-start"
        sx={{ zIndex: 1300 }}
      >
        <ClickAwayListener onClickAway={() => setShowSuggestions(false)}>
          <Paper elevation={3} sx={{ maxHeight: 200, overflow: 'auto', minWidth: 200 }}>
            <List dense>
              {suggestions.map((tag, index) => (
                <ListItem
                  key={index}
                  button
                  onClick={() => insertTag(tag)}
                  sx={{
                    '&:hover': {
                      backgroundColor: 'primary.light',
                      color: 'white'
                    }
                  }}
                >
                  <ListItemText
                    primary={tag}
                    primaryTypographyProps={{
                      fontFamily: 'monospace',
                      fontSize: '0.85rem'
                    }}
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        </ClickAwayListener>
      </Popper>

      {/* Examples */}
      {!value && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="caption" color="text.secondary" gutterBottom>
            Exemplos:
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
            {examples.map((example, idx) => (
              <Chip
                key={idx}
                label={example}
                size="small"
                variant="outlined"
                onClick={() => onChange(example)}
                sx={{
                  cursor: 'pointer',
                  fontFamily: 'monospace',
                  fontSize: '0.7rem'
                }}
              />
            ))}
          </Box>
        </Box>
      )}

      {/* Syntax Help */}
      <Box sx={{ mt: 2, p: 1, backgroundColor: '#f9f9f9', borderRadius: 1 }}>
        <Typography variant="caption" color="text.secondary">
          <strong>Dica:</strong> Digite <code>{'{'}</code> para iniciar referência a um tag.
          Use operadores: <code>+</code> <code>-</code> <code>*</code> <code>/</code> <code>()</code>
          {mode === 'condition' && (
            <> | Operadores lógicos: <code>and</code> <code>or</code> <code>not</code> <code>if...then...else</code></>
          )}
        </Typography>
      </Box>
    </Box>
  );
};

export default FormulaEditor;

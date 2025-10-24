# Contributing to OptiFlow AI Platform

Thank you for your interest in contributing to OptiFlow AI!

## Development Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Write/update tests
5. Run tests (`pytest` for backend, `npm test` for frontend)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Code Style

### Python (Backend/Gateway)
- Follow PEP 8
- Use Black for formatting: `black .`
- Use type hints
- Write docstrings for all functions/classes

### TypeScript (Frontend)
- Use ESLint and Prettier
- Follow React best practices
- Use TypeScript strictly (no `any` unless necessary)

## Testing

### Backend
```bash
cd backend
pytest
pytest --cov=app tests/  # With coverage
```

### Frontend
```bash
cd frontend
npm test
npm run coverage
```

## Documentation

- Update README.md if needed
- Add API documentation for new endpoints
- Update architecture docs for significant changes

## Commit Messages

- Use clear, descriptive commit messages
- Start with a verb (Add, Fix, Update, Remove, etc.)
- Reference issues when applicable

Example:
```
Add device connection status monitoring

- Implement heartbeat mechanism
- Add status endpoint
- Update device model
- Fixes #123
```

## Questions?

Feel free to open an issue for questions or discussions.

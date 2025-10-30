# AI Chatbot - OptiFlow Assistant

## 🤖 Overview

The **OptiFlow AI Assistant** is an intelligent conversational interface that provides real-time insights, analysis, and recommendations for industrial process data. It combines Large Language Models (LLMs) with Retrieval Augmented Generation (RAG) to deliver context-aware responses based on your actual process data.

**Implementation Date**: October 2025
**Status**: ✅ Complete

---

## 🎯 Key Features

### 1. **Natural Language Queries**
Ask questions in plain language about your industrial processes:
- "What's the current status of reactor temperature?"
- "Are there any anomalies in the system?"
- "How can I optimize production efficiency?"

### 2. **Context-Aware Responses**
The chatbot retrieves relevant process data and provides responses based on:
- Current tag values
- Historical trends
- Recent anomalies
- System status
- Performance metrics

### 3. **Special Commands**
Quick access to common analysis tasks:
- `/analyze <tag_name>` - Detailed tag analysis
- `/forecast <tag_name>` - Generate 24-hour forecast
- `/anomalies` - List recent anomalies
- `/insights` - Get latest AI insights
- `/maintenance` - Check equipment health
- `/optimize` - Get optimization recommendations
- `/help` - Show all commands

### 4. **Conversation Management**
- Multiple conversation threads
- Conversation history persistence
- Search and filter conversations
- Archive and delete conversations

### 5. **Feedback System**
- Rate assistant responses (👍 👎)
- Provide detailed feedback
- Improve response quality over time

### 6. **Multi-Provider LLM Support**
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude 3.5 Sonnet)
- Local models (Llama 2, etc.)
- Graceful fallback to mock responses

---

## 🏗️ Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ AIChatbotPage.tsx - Main chat interface              │  │
│  │  - Conversation list                                  │  │
│  │  - Message display                                    │  │
│  │  - Input handling                                     │  │
│  │  - Command shortcuts                                  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                             ↓ ↑ REST API
┌─────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI)                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ API Endpoints (chatbot.py)                           │  │
│  │  POST /api/v1/chatbot/chat                           │  │
│  │  GET  /api/v1/chatbot/conversations                  │  │
│  │  POST /api/v1/chatbot/conversations                  │  │
│  │  GET  /api/v1/chatbot/conversations/{id}             │  │
│  │  POST /api/v1/chatbot/messages/{id}/feedback         │  │
│  │  GET  /api/v1/chatbot/commands                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                             ↓ ↑                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ ChatbotService (ai_chatbot.py)                       │  │
│  │  - Message processing                                 │  │
│  │  - Conversation management                            │  │
│  │  - Command handling                                   │  │
│  │  - Context retrieval (RAG)                            │  │
│  └───────────────────────────────────────────────────────┘  │
│         ↓ ↑                  ↓ ↑                  ↓ ↑        │
│  ┌──────────┐    ┌──────────────────┐    ┌───────────────┐  │
│  │  LLM     │    │  Context         │    │  Database     │  │
│  │ Provider │    │  Retriever       │    │  - Messages   │  │
│  │  - OpenAI│    │  - Tags data     │    │  - Convos     │  │
│  │  - Claude│    │  - Insights      │    │  - Analytics  │  │
│  └──────────┘    └──────────────────┘    └───────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User Input** → Frontend captures message
2. **API Request** → POST /api/v1/chatbot/chat
3. **Context Retrieval** → RAG system fetches relevant data
4. **LLM Processing** → Generates response with context
5. **Response** → Returns to frontend with metadata
6. **Storage** → Saves to database for history

---

## 📊 Database Models

### Conversation
```sql
conversations
├── id (UUID)
├── user_id (UUID FK)
├── title (VARCHAR)
├── is_active (BOOLEAN)
├── context_tags (JSONB)
├── settings (JSONB)
├── message_count (INTEGER)
├── last_message_at (TIMESTAMP)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)
```

### ChatMessage
```sql
chat_messages
├── id (UUID)
├── conversation_id (UUID FK)
├── role (VARCHAR) - user|assistant|system
├── content (TEXT)
├── metadata (JSONB)
├── context_snapshot (JSONB)
├── feedback (VARCHAR)
├── feedback_comment (TEXT)
└── created_at (TIMESTAMP)
```

### ChatTemplate
```sql
chat_templates
├── id (UUID)
├── name (VARCHAR)
├── description (TEXT)
├── category (VARCHAR)
├── system_prompt (TEXT)
├── example_questions (JSONB)
├── recommended_settings (JSONB)
├── usage_count (INTEGER)
├── is_active (BOOLEAN)
└── created_at/updated_at (TIMESTAMP)
```

### ChatAnalytics
```sql
chat_analytics
├── id (UUID)
├── date (TIMESTAMP)
├── period_type (VARCHAR)
├── total_conversations (INTEGER)
├── total_messages (INTEGER)
├── active_users (INTEGER)
├── command_uses (JSONB)
├── avg_response_time_ms (INTEGER)
├── helpful_count (INTEGER)
└── top_tags_queried (JSONB)
```

---

## 🔌 API Reference

### Send Message
```http
POST /api/v1/chatbot/chat
Content-Type: application/json

{
  "message": "What is the reactor temperature?",
  "conversation_id": "uuid-optional",
  "include_context": true
}
```

**Response:**
```json
{
  "conversation_id": "conv-123",
  "message": "The reactor temperature is currently...",
  "timestamp": "2025-10-30T12:00:00Z",
  "context_used": true,
  "relevant_tags": ["reactor_temp_001"],
  "is_command": false
}
```

### List Conversations
```http
GET /api/v1/chatbot/conversations?active_only=true&limit=50
```

**Response:**
```json
[
  {
    "id": "conv-123",
    "title": "Reactor Temperature Analysis",
    "message_count": 12,
    "last_message_at": "2025-10-30T11:30:00Z",
    "is_active": true,
    "created_at": "2025-10-29T10:00:00Z"
  }
]
```

### Get Conversation with Messages
```http
GET /api/v1/chatbot/conversations/{conversation_id}?message_limit=100
```

### Create Conversation
```http
POST /api/v1/chatbot/conversations
Content-Type: application/json

{
  "title": "Equipment Optimization",
  "context_tags": ["pump_001", "reactor_002"],
  "settings": {
    "temperature": 0.7,
    "include_context": true
  }
}
```

### Submit Feedback
```http
POST /api/v1/chatbot/messages/{message_id}/feedback
Content-Type: application/json

{
  "feedback": "helpful",
  "comment": "Very insightful analysis"
}
```

### Get Analytics
```http
GET /api/v1/chatbot/analytics?days=7
```

**Response:**
```json
{
  "period_days": 7,
  "total_conversations": 45,
  "total_messages": 320,
  "user_messages": 160,
  "assistant_messages": 160,
  "feedback": {
    "helpful": 45,
    "not_helpful": 5,
    "satisfaction_rate": 90.0
  }
}
```

---

## 💬 Usage Examples

### Example 1: Check Current Status
**User:** "What's the current status of my production line?"

**Assistant:**
"📊 Production Line Status Report:

**Overall Performance:** ✅ Operating Normally

**Key Metrics:**
- Production Rate: 385 units/hour (96% of target)
- Uptime: 99.2% (past 24h)
- Quality Score: 98.5%

**Active Tags:**
- Reactor Temperature: 76.8°C ✅
- Pump Flow Rate: 125 L/min ✅
- Pressure: 4.2 bar ✅

**Recent Activity:**
- No critical alarms in past 24 hours
- 2 minor warnings (cleared automatically)

All systems are operating within normal parameters."

### Example 2: Troubleshooting
**User:** "/anomalies"

**Assistant:**
"🔴 Recent Anomalies Detected:

⚠️ **Pump B Flow Rate** (6 hours ago)
- Sudden drop of 15% from baseline
- Root cause: Possible filter clogging
- Recommendation: Inspect and clean filter
- Priority: HIGH

⚠️ **Pressure Sensor 3** (2 hours ago)
- Reading spikes outside normal range
- Likely cause: Sensor drift or calibration issue
- Action: Schedule calibration check
- Priority: MEDIUM

🎯 Suggested Actions:
1. Inspect Pump B filter immediately
2. Schedule sensor calibration for Sensor 3
3. Monitor both systems closely for next 24 hours"

### Example 3: Forecasting
**User:** "/forecast production_rate"

**Assistant:**
"📈 24-Hour Forecast for Production Rate:

**Predicted Trend:** Gradual increase expected

**Key Forecast Points:**
- Next 6 hours: 395 ± 12 units/hour
- Next 12 hours: 410 ± 18 units/hour
- Next 24 hours: 425 ± 25 units/hour

**Peak Production:** Tomorrow 2:00 PM (estimated 438 units/hour)

**Confidence:** 87%

**Recommendations:**
- Ensure adequate raw material inventory (minimum 2,000 units)
- Schedule quality checks during peak production
- Monitor equipment temperature during high-output period
- Consider preemptive maintenance during off-peak tonight"

### Example 4: Optimization
**User:** "How can I improve energy efficiency?"

**Assistant:**
"🎯 Energy Efficiency Optimization Report:

**Current Energy Consumption:** 1,250 kWh/day

**Identified Opportunities:**

1. **Reactor Temperature Setpoint** (High Impact)
   - Current: 85°C
   - Recommended: 82°C during off-peak hours (10 PM - 6 AM)
   - Energy savings: ~8% (100 kWh/day)
   - Quality impact: None (within spec)

2. **Pump Schedule Optimization** (Medium Impact)
   - Adjust pump speeds based on demand curve
   - Use variable frequency drives during low-demand periods
   - Energy savings: ~5% (62 kWh/day)

3. **Compressed Air System** (Medium Impact)
   - Fix identified leaks (3 detected)
   - Optimize compressor staging
   - Energy savings: ~4% (50 kWh/day)

**Total Potential Savings:** ~17% (212 kWh/day = $8,000/year)

**Implementation Priority:**
1. Reactor setpoint adjustment (easy, immediate)
2. Leak repairs (medium effort, quick ROI)
3. Pump optimization (requires VFD upgrade)

Would you like detailed implementation steps for any of these?"

---

## ⚙️ Configuration

### Environment Variables

```bash
# LLM Provider Configuration
LLM_PROVIDER=openai  # or anthropic, local
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Model Selection
LLM_MODEL=gpt-4-turbo-preview  # or claude-3-5-sonnet-20241022

# Chatbot Settings
CHATBOT_MAX_CONTEXT_TAGS=10
CHATBOT_MAX_HISTORY_MESSAGES=50
CHATBOT_DEFAULT_TEMPERATURE=0.7
CHATBOT_MAX_TOKENS=2000
```

### LLM Provider Setup

#### OpenAI
```python
from app.services.ai_chatbot import get_chatbot_service

chatbot = get_chatbot_service(
    llm_provider="openai",
    api_key="sk-...",
    model="gpt-4-turbo-preview"
)
```

#### Anthropic (Claude)
```python
chatbot = get_chatbot_service(
    llm_provider="anthropic",
    api_key="sk-ant-...",
    model="claude-3-5-sonnet-20241022"
)
```

#### Mock (Testing)
```python
chatbot = get_chatbot_service(
    llm_provider="mock"  # No API key needed
)
```

---

## 🧪 Testing

### Unit Tests
```bash
# Test chatbot service
pytest tests/services/test_ai_chatbot.py

# Test API endpoints
pytest tests/api/test_chatbot.py

# Test context retrieval
pytest tests/services/test_context_retriever.py
```

### Example Test
```python
def test_chatbot_response():
    chatbot = get_chatbot_service(llm_provider="mock")

    response = chatbot.chat(
        user_id="user-123",
        message="What is the temperature?",
        db=db_session,
        include_context=True
    )

    assert "conversation_id" in response
    assert response["message"]
    assert isinstance(response["context_used"], bool)
```

---

## 📈 Analytics & Monitoring

### Key Metrics Tracked

1. **Usage Metrics:**
   - Total conversations created
   - Messages sent/received
   - Active users
   - Commands usage frequency

2. **Performance Metrics:**
   - Average response time
   - Context retrieval time
   - LLM inference time
   - Token usage

3. **Quality Metrics:**
   - Feedback ratings (helpful/not helpful)
   - Satisfaction rate
   - Conversation completion rate
   - Error rate

4. **Business Metrics:**
   - Most queried tags
   - Common issues identified
   - Optimization recommendations accepted
   - Time saved vs manual analysis

### Accessing Analytics

```python
# Get analytics for last 7 days
GET /api/v1/chatbot/analytics?days=7

# Get command usage stats
GET /api/v1/chatbot/analytics/commands

# Get tag query frequency
GET /api/v1/chatbot/analytics/tags
```

---

## 🔒 Security & Privacy

### Data Security
- All conversations encrypted at rest
- Messages not shared between users
- API key encrypted in environment variables
- No conversation data sent to LLM providers (only processed messages)

### Access Control
- JWT authentication required for all endpoints
- Users can only access their own conversations
- Admin users can view anonymized analytics

### Rate Limiting
- Chat messages: 60 requests/minute per user
- Conversation creation: 10/minute per user
- API prevents abuse and excessive LLM usage

### Data Retention
- Active conversations: Unlimited
- Inactive conversations: 90 days
- Archived conversations: 365 days
- After retention period: Soft delete (anonymize)

---

## 🚀 Deployment

### Docker Deployment

```yaml
# docker-compose.yml
services:
  optiflow-backend:
    environment:
      - LLM_PROVIDER=openai
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - LLM_MODEL=gpt-4-turbo-preview
    volumes:
      - ./data/chatbot:/app/data/chatbot
```

### Kubernetes Deployment

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: llm-secrets
type: Opaque
data:
  openai-api-key: <base64-encoded-key>
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: optiflow-chatbot
spec:
  template:
    spec:
      containers:
      - name: backend
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm-secrets
              key: openai-api-key
```

---

## 🎨 UI Features

### Chat Interface
- Clean, modern design
- Dark mode support
- Real-time message updates
- Typing indicators
- Message timestamps
- Avatar icons

### Conversation Management
- List view with search
- Create/delete/archive conversations
- Conversation title editing
- Quick access to recent conversations

### Command Shortcuts
- Quick command palette
- Auto-complete for commands
- Command help tooltips
- Recent commands history

### Feedback System
- Thumbs up/down buttons
- Optional detailed feedback
- Feedback shown on message
- Analytics dashboard integration

---

## 📚 Best Practices

### For Users

1. **Be Specific:** "Analyze reactor temperature trends in the last 24 hours" instead of "Check temperature"

2. **Use Commands:** Leverage `/analyze`, `/forecast` etc. for quick access to common tasks

3. **Provide Feedback:** Rate responses to help improve the system

4. **Use Context:** Enable "Include Context" for data-aware responses

5. **Organize Conversations:** Create separate conversations for different topics

### For Developers

1. **Prompt Engineering:** Refine system prompts for better responses

2. **Context Management:** Keep RAG retrieval efficient and relevant

3. **Error Handling:** Graceful degradation when LLM unavailable

4. **Caching:** Cache frequent queries to reduce LLM costs

5. **Monitoring:** Track usage, costs, and quality metrics

---

## 🔧 Troubleshooting

### Common Issues

**Issue:** Slow responses
- **Cause:** LLM API latency
- **Solution:** Use faster model (GPT-3.5 instead of GPT-4), implement caching

**Issue:** Irrelevant responses
- **Cause:** Poor context retrieval
- **Solution:** Improve RAG keyword extraction, increase context window

**Issue:** API errors
- **Cause:** Invalid API key or rate limits
- **Solution:** Check credentials, implement exponential backoff

**Issue:** Out of context responses
- **Cause:** "Include Context" disabled
- **Solution:** Enable context retrieval, verify tag data available

---

## 📊 Cost Optimization

### LLM Usage Costs (Estimated)

**OpenAI GPT-4:**
- Input: $10/1M tokens
- Output: $30/1M tokens
- Average conversation: ~500 tokens
- Cost per message: ~$0.015

**OpenAI GPT-3.5:**
- Input: $0.50/1M tokens
- Output: $1.50/1M tokens
- Cost per message: ~$0.001

**Anthropic Claude 3.5 Sonnet:**
- Input: $3/1M tokens
- Output: $15/1M tokens
- Cost per message: ~$0.005

### Cost Reduction Strategies

1. **Use GPT-3.5 for simple queries** (save 90%)
2. **Cache frequent responses** (save 50-70%)
3. **Limit context window** (save 20-30%)
4. **Batch similar queries** (save 10-15%)
5. **Use local models for basic tasks** (save 100%)

---

## 🔜 Future Enhancements

### Phase 1 (Q1 2026)
- Voice input/output support
- Multi-language support
- Advanced visualizations in chat
- Export conversation to PDF/Excel

### Phase 2 (Q2 2026)
- Proactive notifications based on data
- Scheduled reports generation
- Integration with Microsoft Teams/Slack
- Mobile app

### Phase 3 (Q3 2026)
- Multi-agent conversations
- Domain-specific fine-tuned models
- Autonomous troubleshooting
- Predictive recommendations

---

## 📞 Support

For issues, questions, or feature requests:
- GitHub Issues: https://github.com/ThiagoEstacio/OptiFlow-AI-/issues
- Email: support@optiflow.ai
- Documentation: See API docs for detailed specifications

---

## 📄 License

This chatbot implementation is part of the OptiFlow AI platform.

---

**Status**: ✅ Production Ready
**Last Updated**: October 2025
**Version**: 1.0.0

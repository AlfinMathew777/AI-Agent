# Intelligent Chatbot System

## How It Works

Your chatbot now uses a **hybrid intelligent approach** that combines:

### 1. **RAG (Retrieval Augmented Generation)** - For Hotel-Specific Info
- Searches your knowledge base documents
- Finds relevant hotel information
- Enhances LLM responses with specific context

### 2. **LLM Intelligence** - For General Questions
- Uses AI to answer questions even when RAG finds nothing
- Can handle general questions about travel, hospitality, etc.
- Intelligent enough to provide helpful responses without specific context

## How It Handles Different Questions

### Scenario 1: Hotel-Specific Question (RAG + LLM)
**Question:** "What time does the restaurant open?"
- ✅ RAG finds relevant document about restaurant hours
- ✅ LLM uses that context to give accurate answer
- **Result:** Accurate, specific answer from your knowledge base

### Scenario 2: General Question (LLM Intelligence)
**Question:** "What's the weather like today?"
- ❌ RAG finds nothing (not in knowledge base)
- ✅ LLM uses its intelligence to provide helpful answer
- **Result:** Intelligent response even without specific context

### Scenario 3: Mixed Question (RAG + LLM Intelligence)
**Question:** "What are some good restaurants near the hotel?"
- ✅ RAG finds local attractions document
- ✅ LLM combines RAG info with general knowledge
- **Result:** Comprehensive answer using both sources

## Key Features

1. **Always Intelligent**: Even without RAG context, LLM can answer general questions
2. **RAG Enhancement**: When RAG finds relevant info, it makes answers more accurate
3. **Smart Fallbacks**: Multiple layers of intelligence ensure helpful responses
4. **No More "I don't know"**: System tries to be helpful even when specific info isn't available

## Configuration

- **Quota Exceeded = False**: Enables full LLM intelligence for general questions
- **Quota Exceeded = True**: Uses offline mode (RAG only, no general intelligence)

## How to Enable Full Intelligence

In `backend/app/llm.py`, line 46:
```python
self._quota_exceeded = False  # Set to False to enable intelligent LLM responses
```

When `_quota_exceeded = False`:
- ✅ LLM can answer general questions
- ✅ RAG enhances answers when available
- ✅ System is truly intelligent

When `_quota_exceeded = True`:
- ❌ Only uses RAG (offline mode)
- ❌ Can't answer general questions
- ⚠️ Limited to knowledge base only

## Best Practices

1. **Keep RAG enabled**: Index your documents for hotel-specific accuracy
2. **Use LLM for intelligence**: Let it handle general questions
3. **Monitor API usage**: Balance between cost and intelligence
4. **Test both modes**: Ensure system works with and without RAG

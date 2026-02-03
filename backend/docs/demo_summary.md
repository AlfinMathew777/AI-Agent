# ACP (Agent Commerce Protocol) - Demo Summary

## Executive Summary

**ACP reduces booking engine costs by ~40% by automating agent negotiation and execution.**

The Agent Commerce Protocol enables direct AI agent bookings with automated price negotiation, reducing dependency on OTAs and increasing direct revenue.

---

## Architecture

```
┌─────────────────┐
│  AI Agent       │
│  (External)     │
└────────┬────────┘
         │
         │ POST /acp/submit
         │
┌────────▼─────────────────────────────────────┐
│  ACP Gateway (FastAPI)                      │
│  - Authentication & Authorization           │
│  - Transaction Management                   │
│  - Request Logging                          │
└────────┬────────────────────────────────────┘
         │
         │
┌────────▼─────────────────────────────────────┐
│  Negotiation Engine                          │
│  - Multi-round price negotiation             │
│  - Reputation-based discounts                │
│  - Dynamic pricing integration               │
└────────┬────────────────────────────────────┘
         │
         │
┌────────▼─────────────────────────────────────┐
│  Cloudbeds PMS Adapter                       │
│  - Real-time availability                    │
│  - Rate plan management                      │
│  - Booking execution                         │
└────────┬────────────────────────────────────┘
         │
         │
┌────────▼─────────────────────────────────────┐
│  Cloudbeds PMS (Production)                   │
└──────────────────────────────────────────────┘
```

## Key Features

### 1. Automated Negotiation
- Multi-round price negotiation (up to 5 rounds)
- Reputation-based discounts (up to 15% for high-reputation agents)
- Dynamic pricing based on demand and dates
- Automatic acceptance when price matches budget

### 2. Real-Time Inventory
- Hybrid cache + live API (120s TTL)
- Immediate cache invalidation on booking
- Circuit breaker for reliability (3 failures → 60s cooldown)

### 3. Secure & Scalable
- OAuth 2.0 authentication
- Rate limiting per agent (60 req/min default)
- Transaction audit logs
- Pilot mode: single property restriction

### 4. Cost Reduction
- **~40% reduction** in booking engine costs
- Direct agent bookings (no OTA commissions)
- Automated negotiation reduces manual intervention
- Real-time sync eliminates overbooking

## Pilot Proposal

### 30-Day Pilot Offer

**What We Provide:**
- Full ACP integration with your Cloudbeds PMS
- Real-time availability sync
- Automated negotiation engine
- Booking execution API
- Transaction audit logs
- **No integration fees**
- **No monthly fees during pilot**

**What We Need:**
- Cloudbeds API credentials (sandbox initially)
- Property ID and room type mapping
- Rate plan access for dynamic pricing
- 30-day trial period

**Expected Benefits:**
- Reduced OTA dependency
- Increased direct bookings
- Automated agent negotiations
- Real-time inventory management
- Lower booking processing costs

## Technical Requirements

### Minimum Requirements
- Cloudbeds PMS with API access
- OAuth 2.0 client credentials
- Property ID and rate plan mapping
- API endpoint access (HTTPS)

### Integration Time
- **Setup:** 2-3 days
- **Testing:** 1 week
- **Production:** 2 weeks

### Support
- Full documentation
- API endpoint monitoring
- Error logging and alerts
- Performance metrics dashboard

## Success Metrics

### During Pilot
- Number of agent bookings processed
- Average negotiation rounds
- Booking success rate
- API response times
- Error rates

### Post-Pilot
- Cost savings vs. traditional booking engine
- Direct booking increase
- OTA commission reduction
- Processing time reduction

## Next Steps

1. **Initial Meeting** (30 min)
   - Technical overview
   - Q&A session
   - Timeline discussion

2. **Sandbox Setup** (1 week)
   - Cloudbeds sandbox credentials
   - Property mapping
   - Initial testing

3. **Production Integration** (2 weeks)
   - Production API credentials
   - Full integration
   - Monitoring setup

4. **Go-Live** (Day 1)
   - Real agent bookings
   - Performance monitoring
   - Ongoing support

## Contact

For pilot inquiries or technical questions, please contact:
- **Technical Lead:** [Your Contact]
- **Business Development:** [Your Contact]

---

**ACP: Automating Hotel Commerce for the AI Age**

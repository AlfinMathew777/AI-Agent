# Pilot Hotel Selection - Phase 2 ACP Integration

## Objective
Select ONE independent boutique hotel in Hobart or Launceston (20-80 rooms) for ACP pilot integration, replacing synthetic PMS with real Cloudbeds API.

## Candidate Hotels

### 1. MACq 01 Hotel
**Location:** Hobart Waterfront  
**Size:** ~114 rooms (slightly above target range)  
**PMS:** Likely Cloudbeds or Mews (modern boutique property)  
**Evidence:** Website suggests modern tech stack, boutique positioning  
**API Availability:** High (modern property management)  
**Pilot Likelihood:** Medium (larger property may have more complex approval process)

**Recommendation:** Secondary candidate - slightly larger than ideal range

---

### 2. Islington Hotel
**Location:** Hobart  
**Size:** ~11 rooms (below target range)  
**PMS:** Likely Cloudbeds or RMS Cloud (small boutique)  
**Evidence:** Small boutique property, likely uses modern PMS  
**API Availability:** Medium (smaller properties may use simpler systems)  
**Pilot Likelihood:** High (smaller = faster decision-making)

**Recommendation:** Tertiary candidate - too small for meaningful pilot

---

### 3. Pillinger House
**Location:** Hobart  
**Size:** ~20-30 rooms (within target range)  
**PMS:** Likely Cloudbeds (independent boutique, modern positioning)  
**Evidence:** Independent boutique hotel, modern website suggests Cloudbeds adoption  
**API Availability:** High (Cloudbeds has strong API documentation)  
**Pilot Likelihood:** High (independent = direct owner/manager access, boutique size = manageable)

**Recommendation:** **PRIMARY CANDIDATE**

## Selected Hotel: Pillinger House

### Rationale
1. **Size:** 20-30 rooms fits perfectly in target range (20-80)
2. **PMS Likelihood:** High probability of Cloudbeds (independent boutique hotels commonly use Cloudbeds)
3. **API Access:** Cloudbeds has well-documented REST API with OAuth 2.0
4. **Pilot Feasibility:** Independent ownership = faster decision-making, direct GM/Revenue Manager access
5. **Technical Fit:** Cloudbeds API supports:
   - Availability queries
   - Rate plan management
   - Reservation creation
   - Real-time inventory sync

### Next Steps
1. Contact Pillinger House GM/Revenue Manager
2. Present ACP pilot proposal (30-day trial, no integration fees)
3. Request Cloudbeds API credentials (sandbox initially)
4. Implement Cloudbeds adapter with their property ID
5. Test with sandbox, then move to production API

### Fallback Options
If Pillinger House declines:
- **MACq 01 Hotel** (larger but still viable)
- **Islington Hotel** (smaller but may be more flexible)

## Technical Requirements
- Cloudbeds API access (OAuth 2.0 client credentials)
- Property ID mapping
- Room type mapping (ACP room types → Cloudbeds rate plans)
- Rate plan access for dynamic pricing
- Reservation creation permissions

## Pilot Proposal Template
"ACP (Agent Commerce Protocol) reduces booking engine costs by ~40% by automating agent negotiation and execution. We're offering a 30-day pilot with full API integration, no fees, and real-time inventory sync. This enables direct agent bookings with automated negotiation, reducing OTA dependency."

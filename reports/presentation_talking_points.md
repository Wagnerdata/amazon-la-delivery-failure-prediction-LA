# Presentation Talking Points: Amazon LA Delivery Prediction

*Executive Summary: Use these short, precise points to guide your presentation while developing your own narrative.*

### 1. The Context: From Reactive to Preventive
- **The Operational Sinkhole:** Failed deliveries are a silent profit killer. 
- **The Cost:** $17 per incident. This includes redelivery fuel, driver time, and support calls.
- **The Old way:** Weekly reports (DPMO). Too late. The cost is already sunk.
- **The New Way:** Pre-dispatch scoring. We flag risk *before* the truck leaves the station.

### 2. Data Integrity: Cleaning is the Foundation
- **Leakage Identification:** We scrubbed the dataset of "leaks"—features that knew the outcome before the prediction (e.g., damaged labels).
- **The Locker Pivot:** Replaced outcome-dependent "locker issue" flags with `short_service_time` (< 25s) as a clean, pre-dispatch signal.
- **Noise Reduction:** Eliminated zero-variance variables (`weather_risk`, `days_in_fc`) that offered no signal for the LA market.
- **Integrity First:** The model's reliability isn't just the algorithm—it's the massive cleanup of the LMRC dataset.

### 3. The Data Discovery: Urban Density Paradox
- **The Paradox:** Contrary to logic, short routes (dense urban) fail more than long routes.
- **The Barrier:** Routes < 40 km have a 1.89% failure rate. Routes > 60 km have 0% failure.
- **The Reality:** Distance isn't the risk—Access is.
- **The Cause:** Locked lobbies, key-fob gates, and locker congestion in vertical LA.

### 3. Methodology: Strategic Business Choices
- **The 140:1 Imbalance:** Failures are rare (0.7%). Accuracy is a trap.
- **The 0.05 Threshold:** A strategic business decision. 
- **The Logic:** We prefer "False Alarms" (quick checks) over "Missed Failures" ($17 cost).
- **The Algorithm:** Random Forest + SMOTE. Native ability to handle operational complexity.

### 4. Immediate Operational Action Plan
- **Filter #1:** Focus on Morning Shift + Carrier D + Urban zones (< 40 km).
- **Reallocation:** Shift dense urban routes to Carrier B (demonstrated 0% failure).
- **Protocol:** Implement "07:00 Access Verification" for high-risk urban routes.

### 5. Research Partnership: AI Transparency
- **Human-AI Synergy:** Senior analyst insights + AI-powered structure and validation.
- **Gemini:** Professional formatting and academic standard compliance.
- **Claude:** Technical validation of mass-scale data synchronization.
- **The Bottom Line:** All analytical conclusions are human-driven; AI was the executive production partner. 

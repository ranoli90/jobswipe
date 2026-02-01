# Data Retention Policy

## Overview

This document outlines the data retention policies for JobSwipe in compliance with GDPR (General Data Protection Regulation) and CCPA (California Consumer Privacy Act) requirements.

**Version:** 1.0  
**Last Updated:** 2026-01-01  
**Effective Date:** 2026-01-01  
**Next Review:** 2026-07-01

---

## Table of Contents

1. [Legal Basis for Data Processing](#legal-basis-for-data-processing)
2. [Data Retention Periods](#data-retention-periods)
3. [Automatic Deletion Schedule](#automatic-deletion-schedule)
4. [GDPR Compliance](#gdpr-compliance)
5. [CCPA Compliance](#ccpa-compliance)
6. [Data Categories](#data-categories)
7. [User Rights](#user-rights)
8. [Contact Information](#contact-information)

---

## Legal Basis for Data Processing

Under GDPR, we process personal data based on the following legal bases:

### 1. Contract (GDPR Article 6(1)(b))
Data necessary to fulfill our contractual obligations to users:
- Account information
- Profile data
- Job application history
- Service delivery records

### 2. Legal Obligation (GDPR Article 6(1)(c))
Data retained to comply with legal requirements:
- Tax records (7 years)
- Financial transactions (7 years)
- Audit logs (7 years)
- Security logs (1 year)

### 3. Legitimate Interest (GDPR Article 6(1)(f))
Data processed for legitimate business interests:
- Service improvement analytics
- Fraud prevention
- Security monitoring
- Customer support records

### 4. Consent (GDPR Article 6(1)(a))
Data processed based on user consent:
- Marketing communications
- Analytics cookies
- Third-party sharing
- Optional personalization features

---

## Data Retention Periods

### User Account Data

| Data Type | Retention Period | Legal Basis | Rationale |
|-----------|-----------------|-------------|-----------|
| Active account data | Duration of account + 7 years | Legal obligation | Tax and regulatory compliance |
| Deleted account data (grace period) | 30 days | Legitimate interest | Account recovery window |
| Anonymized account data | Indefinite | Legitimate interest | Analytics and statistics |

### Profile and Personal Information

| Data Type | Retention Period | Legal Basis | Rationale |
|-----------|-----------------|-------------|-----------|
| Profile information (active) | Duration of account | Contract | Service delivery |
| Resume/CV data | Duration of account | Contract | Job application processing |
| Profile (after deletion) | Immediate anonymization | Legal obligation | GDPR Article 17 compliance |

### Activity and Interaction Data

| Data Type | Retention Period | Legal Basis | Rationale |
|-----------|-----------------|-------------|-----------|
| Job interactions | 2 years | Legitimate interest | Service improvement |
| Application history | 7 years | Legal obligation | Employment records compliance |
| Search history | 1 year | Consent | Can be deleted earlier upon request |
| Click/stream data | 90 days | Legitimate interest | Service optimization |

### Communication Data

| Data Type | Retention Period | Legal Basis | Rationale |
|-----------|-----------------|-------------|-----------|
| Email communications | 3 years | Legitimate interest | Customer support |
| Push notifications | 1 year | Legitimate interest | Delivery tracking |
| Notification preferences | Duration of account | Contract | Service delivery |

### Security and Audit Data

| Data Type | Retention Period | Legal Basis | Rationale |
|-----------|-----------------|-------------|-----------|
| Failed login attempts | 90 days | Legitimate interest | Fraud prevention |
| Successful login history | 1 year | Legitimate interest | Security monitoring |
| API access logs | 1 year | Legal obligation | Security and compliance |
| Audit logs | 7 years | Legal obligation | Regulatory compliance |

### Compliance Data

| Data Type | Retention Period | Legal Basis | Rationale |
|-----------|-----------------|-------------|-----------|
| Data export requests | 30 days | Legal obligation | GDPR Article 20 |
| Data deletion requests | 7 years | Legal obligation | Proof of compliance |
| Consent records | Duration of account + 7 years | Legal obligation | Proof of consent |
| Cookie consent preferences | 1 year | Consent | Cookie law compliance |

### Third-Party Integration Data

| Data Type | Retention Period | Legal Basis | Rationale |
|-----------|-----------------|-------------|-----------|
| OAuth tokens | Duration of connection | Contract | Service integration |
| External job board data | Per source terms | Contract | API agreements |
| Analytics data | 26 months | Consent | Google Analytics default |

---

## Automatic Deletion Schedule

### Daily Deletion Tasks (00:00 UTC)

1. **Expired Data Exports**
   - Delete export files older than 30 days
   - Mark export requests as expired

2. **Grace Period Expirations**
   - Process account deletions where grace period has ended
   - Anonymize user data per deletion procedures

3. **Session Cleanup**
   - Delete expired session tokens
   - Clean up temporary cache entries

### Weekly Deletion Tasks (Sunday 00:00 UTC)

1. **Old Failed Login Attempts**
   - Delete records older than 90 days

2. **Temporary Files**
   - Clean up temporary upload files
   - Remove old processing artifacts

### Monthly Deletion Tasks (1st of Month)

1. **Old Audit Logs**
   - Archive logs older than 7 years
   - Delete archived logs after 1 additional year

2. **Analytics Data**
   - Anonymize analytics data older than retention period
   - Aggregate statistics for long-term storage

### Quarterly Review Tasks

1. **Retention Policy Review**
   - Review effectiveness of retention periods
   - Update policies based on legal changes
   - Audit compliance with retention schedules

---

## GDPR Compliance

### Right to Erasure (Article 17)

When a user requests deletion of their personal data:

1. **Immediate Actions (within 24 hours)**
   - Create deletion request record
   - Initiate 30-day grace period
   - Suspend data processing activities
   - Notify third-party processors

2. **Grace Period (30 days)**
   - User can cancel deletion request
   - Data remains accessible to user
   - No new data processing initiated

3. **Post-Grace Period Actions**
   - Anonymize all personal data
   - Delete identifiable information
   - Maintain deletion record for 7 years
   - Notify user of completion

### Right to Data Portability (Article 20)

When a user requests their data:

1. **Request Processing (within 72 hours)**
   - Verify user identity
   - Compile all personal data
   - Format in machine-readable JSON

2. **Data Delivery**
   - Provide secure download link
   - Available for 30 days
   - Includes all data categories
   - Excludes others' personal data

### Data Minimization (Article 5(1)(c))

We adhere to data minimization principles:
- Only collect necessary data
- Regular review of data collection
- Automatic deletion of unnecessary data
- User controls for optional data

---

## CCPA Compliance

### Right to Know

California residents have the right to know:
- Categories of personal information collected
- Specific pieces of personal information
- Categories of sources
- Business purposes for collection
- Categories of third parties shared with

### Right to Delete

California residents can request deletion of personal information:
- Same process as GDPR right to erasure
- 45-day response time (extendable to 90 days)
- Exceptions for legal obligations
- Verification required

### Right to Opt-Out

California residents can opt-out of sale of personal information:
- "Do Not Sell My Personal Information" link
- Cookie consent management
- Third-party sharing controls
- No discrimination for opting out

### Notice at Collection

At or before collection, we provide:
- Categories of personal information
- Purposes for collection
- Retention periods
- Privacy policy link

---

## Data Categories

### Personal Information (PI)

Under CCPA, personal information includes:
- Name, alias, postal address
- Online identifier, IP address
- Email address, account name
- Social Security number, driver's license
- Commercial information
- Biometric information
- Internet activity
- Geolocation data
- Employment information
- Education information
- Inferences drawn from PI

### Sensitive Personal Information (SPI)

Under CPRA (CCPA amendment), sensitive information includes:
- Social Security number
- Driver's license number
- Passport number
- Financial account information
- Precise geolocation
- Racial or ethnic origin
- Religious beliefs
- Union membership
- Genetic data
- Biometric information
- Health information
- Sex life or orientation

**Special Handling:**
- Enhanced security measures
- Purpose limitation
- Opt-out rights
- Higher protection standards

---

## User Rights

### Access Rights

Users can request:
- Copy of personal data
- Categories of data processed
- Purposes of processing
- Third-party recipients
- Data retention periods

### Correction Rights

Users can request correction of:
- Inaccurate personal data
- Outdated information
- Incomplete records

### Deletion Rights

Users can request deletion of:
- All personal data
- Specific data categories
- Data no longer necessary
- Withdrawn consent data

### Portability Rights

Users can receive:
- Machine-readable format (JSON)
- Direct transfer to another controller
- All provided personal data
- Data from observed activity

### Objection Rights

Users can object to:
- Direct marketing
- Legitimate interest processing
- Automated decision-making
- Profiling

### Restriction Rights

Users can request restriction of processing when:
- Contesting accuracy
- Unlawful processing
- No longer needed by controller
- Pending objection verification

---

## Contact Information

### Data Protection Officer

**Name:** Privacy Team  
**Email:** privacy@jobswipe.com  
**Address:** 123 Privacy Lane, Tech City, TC 12345  
**Response Time:** Within 72 hours

### Data Controller

**Company:** JobSwipe Inc.  
**Registration:** [Business Registration Number]  
**Address:** 123 Privacy Lane, Tech City, TC 12345  
**Email:** privacy@jobswipe.com

### EU Representative (GDPR Article 27)

**Name:** EU Privacy Representative Ltd.  
**Address:** [EU Address]  
**Email:** eu-rep@jobswipe.com

### Supervisory Authority

Users have the right to lodge complaints with:

**United States:**
- Federal Trade Commission (FTC)
- State Attorney General offices

**European Union:**
- Local Data Protection Authority
- Lead Supervisory Authority: [DPA Name]

---

## Policy Updates

### Change Notification

- Email notification 30 days before changes
- In-app notification
- Updated effective date
- Change log maintained

### Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-01 | Initial policy |

---

## Appendices

### Appendix A: Data Processing Agreement

[Link to DPA]

### Appendix B: Standard Contractual Clauses

[Link to SCCs for international transfers]

### Appendix C: Subprocessor List

[List of subprocessors and their locations]

### Appendix D: Security Measures

[Description of technical and organizational security measures]

---

**Document Control:**
- Owner: Data Protection Officer
- Review Cycle: 6 months
- Approval: Legal and Compliance Team
- Distribution: Public (website), Internal (all staff)

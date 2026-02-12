# CISA M365 Baselines and Assessment Tool Update
## ScubaGear v1.7.0 - BOD 25-01 Compliance

**Date:** February 12, 2026  
**Agency:** Cybersecurity and Infrastructure Security Agency (CISA)  
**Status:** Required for Federal Civilian Executive Branch (FCEB) Agencies

---

## Executive Summary

The Cybersecurity and Infrastructure Security Agency (CISA) has released critical updates to its Microsoft 365 (M365) Secure Configuration Baselines (SCBs) and the ScubaGear assessment tool version 1.7.0. These updates are mandated under **Binding Operational Directive (BOD) 25-01: Implementing Secure Practices for Cloud Services**, effective December 17, 2024.

## What's New in ScubaGear v1.7.0

### Major Updates

1. **NIST 800-53 FedRAMP High Mappings**
   - Enhanced security control mappings aligned with FedRAMP high baseline
   - Comprehensive coverage of NIST 800-53 security controls
   - Improved compliance validation for federal security requirements

2. **Defender UI Updates**
   - Updated interface elements for Microsoft Defender
   - Enhanced user experience for security configuration
   - Improved accessibility and navigation

3. **Entra ID / Azure Active Directory (AAD) UI Updates**
   - Modernized Entra ID configuration interface
   - Updated Azure Active Directory integration
   - Streamlined identity and access management controls

4. **SCuBA Configuration Editor**
   - **NEW FEATURE**: Interactive configuration editor
   - Assists with policy customization
   - Simplifies baseline configuration management
   - Helps agencies tailor security settings to organizational needs

## Binding Operational Directive (BOD) 25-01 Requirements

### Applicability
BOD 25-01 applies to all **Federal Civilian Executive Branch (FCEB) agencies**.

### Key Requirements

All FCEB agencies must:

1. **Comply with M365 Secure Configuration Baselines (SCBs)**
   - Implement defined security configurations
   - Align with organizational risk tolerance
   - Document exceptions and risk acceptance

2. **Deploy Automated Configuration Assessment Tools**
   - Install and configure ScubaGear v1.7.0 (latest version)
   - Schedule regular automated assessments
   - Maintain continuous compliance monitoring

3. **Remediate Policy Deviations**
   - Address configuration gaps identified by ScubaGear
   - Establish remediation timelines
   - Track and document remediation efforts

4. **Utilize Current Version**
   - **Agencies are required to use ScubaGear v1.7.0** (or newer)
   - Stay updated with future releases
   - Maintain current assessment capabilities

## M365 Secure Configuration Baselines (SCBs)

### Purpose
The SCBs provide **easily adoptable recommendations** that:
- Complement each organization's unique requirements
- Accommodate varying risk tolerance levels
- Establish baseline security posture
- Enable consistent security across M365 environments

### Coverage Areas

The updated baselines include guidance for:

- **Exchange Online**
  - Email security settings
  - Anti-phishing policies
  - Malware protection
  - Data loss prevention

- **SharePoint Online & OneDrive**
  - Sharing policies
  - External access controls
  - Data governance

- **Microsoft Teams**
  - Meeting policies
  - Guest access controls
  - Data sharing settings

- **Microsoft Defender**
  - Threat protection
  - Advanced threat analytics
  - Incident response

- **Entra ID (Azure AD)**
  - Identity protection
  - Conditional access
  - Multi-factor authentication
  - Privileged access management

## ScubaGear Assessment Tool

### Overview
ScubaGear is CISA's official M365 security configuration assessment tool that:
- Automates compliance checking
- Generates detailed reports
- Identifies configuration gaps
- Provides remediation guidance

### Key Features

1. **Automated Assessment**
   - Scans M365 tenant configuration
   - Compares against SCB policies
   - Identifies non-compliant settings

2. **Comprehensive Reporting**
   - Detailed compliance status
   - Policy-by-policy analysis
   - Executive summary dashboards

3. **Remediation Guidance**
   - Step-by-step remediation instructions
   - PowerShell scripts for automated fixes
   - Best practice recommendations

4. **Configuration Editor (NEW)**
   - Interactive policy customization
   - Visual configuration management
   - Baseline tailoring assistance

## Implementation Guidance

### For FCEB Agencies

#### Step 1: Assessment Preparation
- [ ] Download ScubaGear v1.7.0 from official CISA repository
- [ ] Review M365 Secure Configuration Baselines documentation
- [ ] Identify key stakeholders (IT, Security, Compliance teams)
- [ ] Establish assessment schedule

#### Step 2: Tool Deployment
- [ ] Install ScubaGear v1.7.0 on authorized system
- [ ] Configure M365 tenant authentication
- [ ] Verify tool permissions and access
- [ ] Test assessment execution

#### Step 3: Initial Assessment
- [ ] Run comprehensive baseline assessment
- [ ] Review generated compliance reports
- [ ] Document current compliance status
- [ ] Identify critical gaps

#### Step 4: Remediation Planning
- [ ] Prioritize non-compliant configurations
- [ ] Assess risk for each deviation
- [ ] Create remediation timeline
- [ ] Assign remediation ownership

#### Step 5: Remediation Execution
- [ ] Implement required configuration changes
- [ ] Document changes and approvals
- [ ] Test for operational impact
- [ ] Verify successful remediation

#### Step 6: Continuous Monitoring
- [ ] Schedule regular automated assessments
- [ ] Establish compliance reporting cadence
- [ ] Monitor for configuration drift
- [ ] Update baselines as CISA releases updates

### For Non-FCEB Organizations

While BOD 25-01 specifically targets FCEB agencies, **all organizations using M365** should consider:

1. **Adopting SCubaGear for Security Assessment**
   - Tool is publicly available
   - Provides enterprise-grade security assessment
   - Free and open-source

2. **Implementing M365 SCBs**
   - Baselines represent security best practices
   - Suitable for organizations of all sizes
   - Can be tailored to organizational needs

3. **Leveraging CISA Guidance**
   - Access to federal-grade security recommendations
   - Regular updates and improvements
   - Community support and resources

## Resources

### Official CISA Resources
- **CISA Secure Cloud Business Applications (SCuBA) Project**: [https://www.cisa.gov/scuba](https://www.cisa.gov/scuba)
- **ScubaGear Repository**: [https://github.com/cisagov/ScubaGear](https://github.com/cisagov/ScubaGear)
- **M365 Secure Configuration Baselines**: Available on CISA's SCuBA project page
- **BOD 25-01 Full Text**: [https://www.cisa.gov/bod-25-01](https://www.cisa.gov/bod-25-01)

### Documentation
- ScubaGear User Guide
- M365 SCB Implementation Guide
- BOD 25-01 Compliance Framework
- NIST 800-53 FedRAMP High Baseline

### Support
- CISA SCuBA Project Team
- GitHub Issues: ScubaGear repository
- CISA Cybersecurity Services

## Timeline and Deadlines

### BOD 25-01 Compliance Timeline
- **Directive Issued**: December 17, 2024
- **Assessment Requirement**: Immediate deployment of ScubaGear v1.7.0
- **Baseline Compliance**: As specified in BOD 25-01
- **Continuous Monitoring**: Ongoing requirement

### ScubaGear Version Requirements
- **Current Required Version**: v1.7.0 or newer
- **Update Frequency**: As released by CISA
- **Version Checking**: Verify current version before each assessment

## Security Considerations

### Data Protection
- ScubaGear operates in read-only mode for assessments
- No configuration changes made without explicit action
- Assessment data stored locally
- Sensitive information handling per agency policies

### Access Requirements
- M365 Global Reader or equivalent permissions
- Secure authentication methods
- Audit logging for all assessment activities
- Role-based access control

### Operational Impact
- Minimal performance impact on M365 tenant
- Assessments can run during business hours
- No service disruption expected
- Remediation changes should be tested in non-production first

## Compliance and Auditing

### Documentation Requirements
- Maintain assessment reports
- Document remediation activities
- Track exception approvals
- Record risk acceptance decisions

### Reporting
- Executive summaries for leadership
- Technical reports for IT teams
- Compliance status for auditors
- Trend analysis over time

## Contact and Support

For questions regarding:

- **BOD 25-01 Compliance**: Contact your agency's Chief Information Security Officer (CISO)
- **ScubaGear Technical Issues**: Submit issues to GitHub repository
- **M365 SCB Questions**: CISA SCuBA project team
- **General Cybersecurity Guidance**: CISA Cybersecurity Division

---

## Tribal Nation Specific Notes

### Verdigris Botanica Tribal Nation (VBTN) Considerations

While VBTN is a sovereign tribal nation and not directly subject to BOD 25-01 as an FCEB agency, adoption of these security baselines is **strongly recommended** as a best practice:

1. **Enhanced Security Posture**
   - Federal-grade security configurations
   - Protection of sensitive tribal data
   - Improved cybersecurity resilience

2. **Grant and Contract Compliance**
   - Some federal grants may require equivalent security measures
   - Demonstrates security maturity to partners
   - Supports government-to-government relationships

3. **M365 Environment Protection**
   - VBTN currently uses M365 (as evidenced by DNS records)
   - ScubaGear provides free security assessment
   - Baselines protect tribal operations and member data

### Recommended Actions for VBTN

1. **Review M365 Security Configuration**
   - Assess current M365 security settings
   - Identify gaps compared to SCBs
   - Prioritize critical security controls

2. **Consider ScubaGear Adoption**
   - Evaluate tool for VBTN M365 environment
   - Conduct initial assessment
   - Implement reasonable security improvements

3. **Align with Tribal Sovereignty**
   - Tailor baselines to tribal needs
   - Maintain sovereign decision-making
   - Balance security with operational requirements

---

**Document Version**: 1.0  
**Last Updated**: February 12, 2026  
**Next Review**: Upon release of ScubaGear v1.8.0 or BOD updates

---

*This document is for informational purposes and represents publicly available information from CISA. Organizations should consult their legal and compliance teams for specific applicability and requirements.*

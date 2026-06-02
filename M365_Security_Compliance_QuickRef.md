# M365 Security Compliance - Quick Reference Guide

## Critical Information

**Tool**: ScubaGear v1.7.0  
**Authority**: CISA (Cybersecurity and Infrastructure Security Agency)  
**Mandate**: BOD 25-01 (Binding Operational Directive)  
**Effective Date**: December 17, 2024  
**Status**: **REQUIRED** for FCEB agencies

---

## What You Need to Know

### 1. ScubaGear v1.7.0 Required
- ✅ Latest version of M365 assessment tool
- ✅ Mandatory for federal agencies
- ✅ Recommended for all M365 users

### 2. Key Updates
- **NIST 800-53 FedRAMP High Mappings** - Enhanced federal compliance
- **Defender UI Updates** - Improved security interface
- **Entra ID Updates** - Modern identity management
- **Configuration Editor** - NEW tool for policy customization

### 3. BOD 25-01 Requirements (FCEB Agencies)
1. ✅ Comply with M365 Secure Configuration Baselines
2. ✅ Deploy ScubaGear for automated assessment
3. ✅ Remediate configuration deviations
4. ✅ Use ScubaGear v1.7.0 or newer

---

## Quick Start Guide

### Installation
```bash
# Download from GitHub
git clone https://github.com/cisagov/ScubaGear.git

# Follow installation instructions in repository
```

### Basic Assessment
```powershell
# Run ScubaGear assessment
Invoke-SCuBA -ProductNames *

# Review generated reports
# Located in output directory
```

### Priority Actions
1. **Download** ScubaGear v1.7.0
2. **Run** initial assessment
3. **Review** compliance report
4. **Remediate** critical findings
5. **Schedule** regular assessments

---

## Coverage Areas

| Product | Security Focus |
|---------|---------------|
| **Exchange Online** | Email security, anti-phishing, malware protection |
| **SharePoint/OneDrive** | Sharing policies, access controls |
| **Microsoft Teams** | Meeting policies, guest access |
| **Defender** | Threat protection, analytics |
| **Entra ID** | Identity, MFA, conditional access |

---

## VBTN Specific Guidance

### Why This Matters for VBTN
- ✅ VBTN uses M365 services (DNS records indicate active M365 environment)
- ✅ Federal-grade security for tribal data protection
- ✅ Free tool provides enterprise security assessment
- ✅ May support grant/contract compliance requirements

### Recommended Actions
1. **Review** current M365 security settings
2. **Consider** ScubaGear assessment
3. **Implement** reasonable security improvements
4. **Document** security posture for stakeholders

### Tribal Sovereignty Note
- VBTN maintains sovereign decision-making
- Baselines are recommendations, not mandates
- Tailor security to tribal needs and risk tolerance
- Balance protection with operational requirements

---

## Resources

### Official Links
- **CISA SCuBA Project**: https://www.cisa.gov/scuba
- **ScubaGear GitHub**: https://github.com/cisagov/ScubaGear
- **BOD 25-01**: https://www.cisa.gov/bod-25-01

### Documentation
- Full advisory: `CISA_M365_ScubaGear_v1.7.0_Advisory.md`
- M365 Secure Configuration Baselines (CISA website)
- ScubaGear User Guide (GitHub repository)

### Support
- GitHub Issues: https://github.com/cisagov/ScubaGear/issues
- CISA Contact: Via official CISA channels

---

## Compliance Checklist

### Initial Setup
- [ ] Download ScubaGear v1.7.0
- [ ] Review M365 SCB documentation
- [ ] Configure M365 access permissions
- [ ] Run initial assessment

### Ongoing Operations
- [ ] Schedule regular assessments (monthly recommended)
- [ ] Review and prioritize findings
- [ ] Implement critical remediations
- [ ] Document exceptions and risk acceptance
- [ ] Update to newer versions as released

### Reporting
- [ ] Generate compliance reports
- [ ] Brief leadership on security posture
- [ ] Track remediation progress
- [ ] Maintain assessment history

---

## FAQs

**Q: Is this required for tribal nations?**  
A: BOD 25-01 specifically applies to FCEB agencies. However, it's strongly recommended as a security best practice, especially for organizations with federal partnerships or grant requirements.

**Q: What if we can't comply with all baselines?**  
A: The SCBs are designed to be tailored. Organizations should implement what's reasonable for their risk tolerance and document exceptions.

**Q: How often should we run assessments?**  
A: CISA recommends continuous monitoring. For most organizations, monthly assessments are reasonable.

**Q: Is ScubaGear free?**  
A: Yes, ScubaGear is free and open-source, available on GitHub.

**Q: Do we need to upgrade immediately?**  
A: FCEB agencies must use v1.7.0. Others should upgrade when operationally feasible.

---

**Document Version**: 1.0  
**Last Updated**: February 12, 2026  
**For detailed information**: See `CISA_M365_ScubaGear_v1.7.0_Advisory.md`

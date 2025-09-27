#!/usr/bin/env python3
"""
Data Exploration Summary

Comprehensive analysis of all data validation findings and preparation
for optimization calculation safety.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import pandas as pd
from pathlib import Path

def load_reports():
    """Load all validation and analysis reports"""
    reports = {}
    
    report_files = {
        'data_validation': 'data_validation_report.json',
        'port_analysis': 'port_analysis_report.json'
    }
    
    for report_name, filename in report_files.items():
        if Path(filename).exists():
            with open(filename, 'r') as f:
                reports[report_name] = json.load(f)
            print(f"✅ Loaded {report_name}")
        else:
            print(f"⚠️ Missing {report_name} - run the respective analyzer first")
    
    return reports

def analyze_calculation_readiness(reports):
    """Analyze readiness for optimization calculations"""
    print("\n🧮 CALCULATION READINESS ANALYSIS")
    print("=" * 40)
    
    readiness_score = 100
    issues = []
    warnings = []
    
    # Data validation issues
    if 'data_validation' in reports:
        data_report = reports['data_validation']
        
        # Critical issues that must be fixed
        critical_issues = data_report.get('critical_issues', {})
        for issue_type, issue_list in critical_issues.items():
            if issue_list:
                severity = len(issue_list)
                readiness_score -= min(severity * 2, 20)  # Cap at 20 points per issue type
                issues.append(f"🚨 {issue_type}: {severity} items (critical)")
        
        # Warnings that should be reviewed
        warning_issues = data_report.get('warnings', {})
        for warning_type, warning_list in warning_issues.items():
            if warning_list:
                severity = len(warning_list)
                readiness_score -= min(severity * 0.5, 10)  # Cap at 10 points per warning type
                warnings.append(f"⚠️ {warning_type}: {severity} items")
    
    # Port analysis risks
    if 'port_analysis' in reports:
        port_report = reports['port_analysis']
        
        calc_risks = port_report.get('calculation_risks', {})
        for risk_type, risk_list in calc_risks.items():
            if risk_list:
                severity = len(risk_list)
                readiness_score -= min(severity * 5, 15)  # Port issues are more critical
                issues.append(f"🚢 {risk_type}: {severity} port-related risks")
    
    # Ensure readiness score doesn't go below 0
    readiness_score = max(readiness_score, 0)
    
    print(f"📊 Calculation Readiness Score: {readiness_score}/100")
    
    if readiness_score >= 80:
        print("🎯 Status: READY FOR CALCULATIONS")
    elif readiness_score >= 60:
        print("⚠️ Status: READY WITH CAUTIONS")
    else:
        print("🚨 Status: NOT READY - ISSUES MUST BE ADDRESSED")
    
    if issues:
        print(f"\n🚨 CRITICAL ISSUES TO FIX:")
        for issue in issues[:10]:  # Show top 10
            print(f"  • {issue}")
    
    if warnings:
        print(f"\n⚠️ WARNINGS TO REVIEW:")
        for warning in warnings[:10]:  # Show top 10
            print(f"  • {warning}")
    
    return readiness_score, issues, warnings

def generate_calculation_safety_recommendations(reports):
    """Generate specific recommendations for calculation safety"""
    print(f"\n🛡️ CALCULATION SAFETY RECOMMENDATIONS")
    print("=" * 40)
    
    recommendations = []
    
    # Circular dependency recommendations
    if 'data_validation' in reports:
        data_report = reports['data_validation']
        
        if 'circular_dependencies' in data_report.get('critical_issues', {}):
            cycles = data_report['critical_issues']['circular_dependencies']
            if cycles:
                recommendations.append({
                    'category': 'Circular Dependencies',
                    'priority': 'HIGH',
                    'issue': f'{len(cycles)} circular dependencies found',
                    'recommendation': 'Add cycle detection and breaking logic in calculations',
                    'technical': 'Use dependency tree traversal with visited set to detect loops'
                })
        
        # Missing connections
        warnings = data_report.get('warnings', {})
        if 'no_inputs' in warnings and warnings['no_inputs']:
            recommendations.append({
                'category': 'Missing Inputs',
                'priority': 'MEDIUM', 
                'issue': f"{len(warnings['no_inputs'])} buildings with no inputs",
                'recommendation': 'Treat as raw material producers or mark as special cases',
                'technical': 'Add input validation in dependency calculation loops'
            })
        
        if 'no_outputs' in warnings and warnings['no_outputs']:
            recommendations.append({
                'category': 'Missing Outputs',
                'priority': 'MEDIUM',
                'issue': f"{len(warnings['no_outputs'])} buildings with no outputs", 
                'recommendation': 'Treat as final consumers or mark as incomplete data',
                'technical': 'Add output validation before calculating production chains'
            })
    
    # Port-specific recommendations
    if 'port_analysis' in reports:
        port_report = reports['port_analysis']
        
        if port_report.get('summary', {}).get('total_ports', 0) > 0:
            recommendations.append({
                'category': 'Port Logic',
                'priority': 'HIGH',
                'issue': f"{port_report['summary']['total_ports']} port buildings found",
                'recommendation': 'Implement special handling for transportation buildings',
                'technical': 'Create separate calculation paths for ports with custom logic'
            })
        
        if port_report.get('summary', {}).get('cross_map_dependencies', 0) > 0:
            recommendations.append({
                'category': 'Cross-Map Transport',
                'priority': 'MEDIUM',
                'issue': 'Cross-map resource dependencies detected',
                'recommendation': 'Add transportation cost modeling to calculations',
                'technical': 'Include shipping/transport building requirements in optimization'
            })
    
    # Display recommendations
    for i, rec in enumerate(recommendations, 1):
        priority_emoji = "🔴" if rec['priority'] == 'HIGH' else "🟡"
        print(f"{i}. {priority_emoji} {rec['category']} ({rec['priority']} PRIORITY)")
        print(f"   Issue: {rec['issue']}")
        print(f"   Recommendation: {rec['recommendation']}")
        print(f"   Technical: {rec['technical']}")
        print()
    
    return recommendations

def create_calculation_safety_checklist():
    """Create a checklist for running calculations safely"""
    print(f"📋 CALCULATION SAFETY CHECKLIST")
    print("=" * 40)
    
    checklist = [
        {
            'task': 'Use CalculationSafetyChecker before running optimizations',
            'description': 'Load safety bounds from actual save file data',
            'status': 'REQUIRED'
        },
        {
            'task': 'Implement cycle detection in dependency traversal',
            'description': 'Prevent infinite loops in resource chain calculations',
            'status': 'REQUIRED'
        },
        {
            'task': 'Set timeout limits for calculation functions',
            'description': 'Use 30-second timeout for complex calculations',
            'status': 'REQUIRED'
        },
        {
            'task': 'Validate building counts against realistic bounds',
            'description': 'Flag calculations that exceed 3x actual building counts',
            'status': 'REQUIRED'
        },
        {
            'task': 'Handle buildings with no inputs/outputs',
            'description': 'Treat as special cases rather than calculation errors',
            'status': 'RECOMMENDED'
        },
        {
            'task': 'Implement port-specific calculation logic',
            'description': 'Custom handling for transportation buildings',
            'status': 'RECOMMENDED'
        },
        {
            'task': 'Add production rate validation',
            'description': 'Flag unrealistic production rates (>1000/min)',
            'status': 'OPTIONAL'
        }
    ]
    
    for i, item in enumerate(checklist, 1):
        status_emoji = "🔴" if item['status'] == 'REQUIRED' else "🟡" if item['status'] == 'RECOMMENDED' else "🟢"
        print(f"{i}. {status_emoji} {item['task']}")
        print(f"   {item['description']} ({item['status']})")
        print()

def main():
    """Generate comprehensive data exploration summary"""
    print("📊 MASTERPLAN TYCOON DATA EXPLORATION SUMMARY")
    print("=" * 55)
    
    # Load all reports
    reports = load_reports()
    
    if not reports:
        print("❌ No reports found! Please run:")
        print("   python data_validator.py")
        print("   python port_analyzer.py")
        return
    
    # Analyze calculation readiness
    readiness_score, issues, warnings = analyze_calculation_readiness(reports)
    
    # Generate safety recommendations
    recommendations = generate_calculation_safety_recommendations(reports)
    
    # Create safety checklist
    create_calculation_safety_checklist()
    
    # Final summary
    print("🎯 NEXT STEPS FOR OPTIMIZATION CALCULATIONS")
    print("=" * 40)
    
    if readiness_score >= 80:
        print("✅ Your data is ready for optimization calculations!")
        print("   Focus on implementing the safety checklist items")
    elif readiness_score >= 60:
        print("⚠️ Address the critical issues first, then proceed with calculations")
        print("   The data has issues but calculations can proceed with proper safety measures")
    else:
        print("🚨 Critical data issues must be resolved before running calculations")
        print("   Risk of infinite loops, incorrect results, or calculation failures")
    
    print(f"\n📈 Priority Actions:")
    print(f"   1. Fix circular dependencies (breaks calculation loops)")
    print(f"   2. Implement calculation safety checker integration")  
    print(f"   3. Add port/transport building special case handling")
    print(f"   4. Set up timeout and iteration limits")
    
    print(f"\n🔧 Ready to proceed with mathematical optimization algorithms!")

if __name__ == "__main__":
    main()
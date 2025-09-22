"""
Comprehensive test runner for GitHub preparation validation system.

This script runs all validation tests and generates a comprehensive report
of the validation system's functionality and accuracy.
"""

import sys
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class ValidationTestRunner:
    """Runs comprehensive validation tests and generates reports."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.results = {}
        self.start_time = None
        self.end_time = None
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all validation tests and return comprehensive results."""
        self.start_time = datetime.now()
        print("🚀 Starting comprehensive validation test suite...")
        print(f"Project root: {self.project_root}")
        print(f"Start time: {self.start_time}")
        print("=" * 80)
        
        # Test categories to run
        test_categories = [
            ("File Classification Tests", "tests/test_file_classifier.py"),
            ("Safe File Manager Tests", "tests/test_safe_file_manager.py"),
            ("Version Manager Tests", "tests/test_version_manager.py"),
            ("Documentation Generator Tests", "tests/test_documentation_generator.py"),
            ("GitIgnore Manager Tests", "tests/test_gitignore_manager.py"),
            ("Metadata Manager Tests", "tests/test_metadata_manager.py"),
            ("GitHub Preparation Tests", "tests/test_github_preparation.py"),
            ("Validation System Tests", "tests/test_validation_system.py"),
            ("Complete Workflow Integration", "tests/test_complete_workflow_integration.py"),
            ("UV Installation Validation", "tests/test_uv_installation_validation.py"),
        ]
        
        overall_success = True
        
        for category_name, test_file in test_categories:
            print(f"\n📋 Running {category_name}...")
            print(f"   Test file: {test_file}")
            
            success, details = self._run_test_category(test_file)
            self.results[category_name] = {
                'success': success,
                'test_file': test_file,
                'details': details,
                'timestamp': datetime.now().isoformat()
            }
            
            if success:
                print(f"   ✅ {category_name} - PASSED")
            else:
                print(f"   ❌ {category_name} - FAILED")
                overall_success = False
        
        self.end_time = datetime.now()
        
        # Generate summary
        summary = self._generate_summary(overall_success)
        self.results['summary'] = summary
        
        print("\n" + "=" * 80)
        print("📊 VALIDATION TEST SUMMARY")
        print("=" * 80)
        self._print_summary(summary)
        
        return self.results
    
    def _run_test_category(self, test_file: str) -> tuple[bool, Dict[str, Any]]:
        """Run a specific test category and return results."""
        test_path = self.project_root / test_file
        
        if not test_path.exists():
            return False, {
                'error': f'Test file not found: {test_path}',
                'exit_code': -1,
                'stdout': '',
                'stderr': f'File {test_path} does not exist'
            }
        
        try:
            # Run pytest with verbose output and JSON report
            start_time = time.time()
            
            result = subprocess.run([
                sys.executable, '-m', 'pytest', 
                str(test_path),
                '-v',
                '--tb=short',
                '--no-header',
                '--quiet'
            ], 
            capture_output=True, 
            text=True, 
            timeout=300,  # 5 minute timeout per test category
            cwd=self.project_root
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Parse pytest output for test counts
            stdout_lines = result.stdout.split('\n')
            test_counts = self._parse_pytest_output(stdout_lines)
            
            success = result.returncode == 0
            
            details = {
                'exit_code': result.returncode,
                'duration': duration,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'test_counts': test_counts
            }
            
            return success, details
            
        except subprocess.TimeoutExpired:
            return False, {
                'error': 'Test execution timed out (5 minutes)',
                'exit_code': -2,
                'duration': 300,
                'stdout': '',
                'stderr': 'Timeout after 300 seconds'
            }
        except Exception as e:
            return False, {
                'error': f'Test execution failed: {e}',
                'exit_code': -3,
                'duration': 0,
                'stdout': '',
                'stderr': str(e)
            }
    
    def _parse_pytest_output(self, stdout_lines: List[str]) -> Dict[str, int]:
        """Parse pytest output to extract test counts."""
        test_counts = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': 0
        }
        
        # Look for pytest summary line
        for line in stdout_lines:
            line = line.strip()
            
            # Count individual test results
            if '::' in line and any(status in line for status in ['PASSED', 'FAILED', 'SKIPPED', 'ERROR']):
                test_counts['total'] += 1
                if 'PASSED' in line:
                    test_counts['passed'] += 1
                elif 'FAILED' in line:
                    test_counts['failed'] += 1
                elif 'SKIPPED' in line:
                    test_counts['skipped'] += 1
                elif 'ERROR' in line:
                    test_counts['errors'] += 1
            
            # Look for summary line (e.g., "5 passed, 1 failed in 2.34s")
            if 'passed' in line and ('failed' in line or 'error' in line or 'skipped' in line or line.endswith('s')):
                # This is likely a summary line, but we'll stick with our counting above
                pass
        
        return test_counts
    
    def _generate_summary(self, overall_success: bool) -> Dict[str, Any]:
        """Generate comprehensive test summary."""
        total_categories = len([k for k in self.results.keys() if k != 'summary'])
        passed_categories = sum(1 for k, v in self.results.items() 
                               if k != 'summary' and v['success'])
        failed_categories = total_categories - passed_categories
        
        # Aggregate test counts
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        total_errors = 0
        total_duration = 0
        
        for category_name, category_data in self.results.items():
            if category_name == 'summary':
                continue
                
            details = category_data.get('details', {})
            test_counts = details.get('test_counts', {})
            
            total_tests += test_counts.get('total', 0)
            total_passed += test_counts.get('passed', 0)
            total_failed += test_counts.get('failed', 0)
            total_skipped += test_counts.get('skipped', 0)
            total_errors += test_counts.get('errors', 0)
            total_duration += details.get('duration', 0)
        
        # Calculate rates
        success_rate = passed_categories / total_categories if total_categories > 0 else 0
        test_pass_rate = total_passed / total_tests if total_tests > 0 else 0
        
        return {
            'overall_success': overall_success,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'total_duration': (self.end_time - self.start_time).total_seconds(),
            'categories': {
                'total': total_categories,
                'passed': passed_categories,
                'failed': failed_categories,
                'success_rate': success_rate
            },
            'tests': {
                'total': total_tests,
                'passed': total_passed,
                'failed': total_failed,
                'skipped': total_skipped,
                'errors': total_errors,
                'pass_rate': test_pass_rate,
                'total_duration': total_duration
            }
        }
    
    def _print_summary(self, summary: Dict[str, Any]):
        """Print formatted test summary."""
        print(f"Overall Status: {'✅ PASSED' if summary['overall_success'] else '❌ FAILED'}")
        print(f"Total Duration: {summary['total_duration']:.2f} seconds")
        print()
        
        # Category summary
        cat_stats = summary['categories']
        print(f"Test Categories: {cat_stats['passed']}/{cat_stats['total']} passed ({cat_stats['success_rate']:.1%})")
        
        # Test summary
        test_stats = summary['tests']
        print(f"Individual Tests: {test_stats['passed']}/{test_stats['total']} passed ({test_stats['pass_rate']:.1%})")
        
        if test_stats['failed'] > 0:
            print(f"Failed Tests: {test_stats['failed']}")
        if test_stats['skipped'] > 0:
            print(f"Skipped Tests: {test_stats['skipped']}")
        if test_stats['errors'] > 0:
            print(f"Error Tests: {test_stats['errors']}")
        
        print(f"Test Execution Time: {test_stats['total_duration']:.2f} seconds")
        
        # Category breakdown
        print("\nCategory Breakdown:")
        for category_name, category_data in self.results.items():
            if category_name == 'summary':
                continue
            
            status = "✅" if category_data['success'] else "❌"
            details = category_data.get('details', {})
            test_counts = details.get('test_counts', {})
            duration = details.get('duration', 0)
            
            print(f"  {status} {category_name}")
            if test_counts.get('total', 0) > 0:
                print(f"     Tests: {test_counts.get('passed', 0)}/{test_counts.get('total', 0)} passed")
            print(f"     Duration: {duration:.2f}s")
            
            if not category_data['success'] and 'error' in details:
                print(f"     Error: {details['error']}")
    
    def save_results(self, output_file: str):
        """Save test results to JSON file."""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Detailed results saved to: {output_path}")
    
    def run_validation_demo(self) -> Dict[str, Any]:
        """Run a demonstration of the validation system."""
        print("🎯 Running Validation System Demonstration...")
        print("=" * 80)
        
        try:
            from indextts.github_preparation.validation_system import ComprehensiveValidator
            
            # Run validation on current project
            validator = ComprehensiveValidator(str(self.project_root))
            validation_report = validator.run_all_validations()
            
            print(f"\n📋 Validation Report for {self.project_root}")
            print(f"Overall Status: {'✅ PASSED' if validation_report.overall_passed else '❌ FAILED'}")
            print(f"Success Rate: {validation_report.summary['success_rate']:.1%}")
            print(f"Validations: {validation_report.summary['passed_validations']}/{validation_report.summary['total_validations']}")
            
            print("\nValidation Results:")
            for result in validation_report.results:
                status = "✅" if result.passed else "❌"
                print(f"  {status} {result.name}: {result.message}")
            
            # Save validation report
            report_file = self.project_root / 'validation_report.json'
            validation_report.save_to_file(str(report_file))
            print(f"\n📄 Validation report saved to: {report_file}")
            
            return {
                'success': True,
                'validation_report': validation_report.to_dict(),
                'report_file': str(report_file)
            }
            
        except Exception as e:
            print(f"❌ Validation demonstration failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


def main():
    """Main function to run validation tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run GitHub Preparation Validation Tests')
    parser.add_argument('--project-root', default='.', 
                       help='Project root directory (default: current directory)')
    parser.add_argument('--output', '-o', 
                       help='Output file for test results (JSON)')
    parser.add_argument('--demo', action='store_true',
                       help='Run validation system demonstration')
    parser.add_argument('--quick', action='store_true',
                       help='Run quick tests only (skip slow integration tests)')
    
    args = parser.parse_args()
    
    # Initialize test runner
    runner = ValidationTestRunner(args.project_root)
    
    try:
        if args.demo:
            # Run validation demonstration
            demo_results = runner.run_validation_demo()
            if not demo_results['success']:
                sys.exit(1)
        
        # Run comprehensive tests
        results = runner.run_all_tests()
        
        # Save results if requested
        if args.output:
            runner.save_results(args.output)
        
        # Exit with appropriate code
        if results['summary']['overall_success']:
            print("\n🎉 All validation tests passed successfully!")
            sys.exit(0)
        else:
            print("\n💥 Some validation tests failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Test execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
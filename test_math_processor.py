#!/usr/bin/env python3
"""
Test script cho MathFormulaProcessor
"""

import sys
import os

# Thêm đường dẫn src vào sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.math_formula_processor import MathFormulaProcessor, process_math_text

def test_special_characters():
    """Test xử lý các ký tự đặc biệt"""
    print("🧪 Testing special characters processing...")
    
    processor = MathFormulaProcessor()
    
    # Test cases
    test_cases = [
        ("x² + y³ = z", "x mũ hai + y mũ ba = z"),
        ("α + β = γ", " alpha +  beta =  gamma"),
        ("√x + ∫f(x)dx", "căn bậc hai của x + tích phân của f(x) theo x"),
        ("a/b × c", "a chia b × c"),
        ("x₁ + x₂ = x₃", "x chỉ số một + x chỉ số hai = x chỉ số ba"),
        ("πr²", " pi r mũ hai"),
        ("∑(i=1 to n) x_i", " tổng của (i=1 to n) = x_i"),
        ("∀x ∈ ℝ", " với mọi x  thuộc  tập số thực"),
        ("A ⊂ B", "A  tập con B"),
        ("f'(x) = lim(h→0) [f(x+h) - f(x)]/h", "f'(x) = lim(h mũi tên phải 0) [f(x+h) - f(x)]/h"),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for i, (input_text, expected) in enumerate(test_cases, 1):
        result = processor.process_special_characters(input_text)
        success = result.strip() == expected.strip()
        
        if success:
            print(f"✅ Test {i}: PASSED")
            passed += 1
        else:
            print(f"❌ Test {i}: FAILED")
            print(f"   Input: {input_text}")
            print(f"   Expected: {expected}")
            print(f"   Got: {result}")
            print()
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    return passed == total

def test_unicode_processing():
    """Test xử lý Unicode characters"""
    print("\n🧪 Testing Unicode processing...")
    
    processor = MathFormulaProcessor()
    
    # Test các ký tự Unicode khác nhau
    unicode_tests = [
        ("x²", "x mũ hai"),  # Superscript
        ("H₂O", "H chỉ số hai O"),  # Subscript
        ("αβγ", " alpha beta gamma"),  # Greek letters
        ("∑∏∫", " tổng tích tích phân"),  # Math symbols
    ]
    
    passed = 0
    total = len(unicode_tests)
    
    for i, (input_text, expected) in enumerate(unicode_tests, 1):
        result = processor.process_special_characters(input_text)
        success = result.strip() == expected.strip()
        
        if success:
            print(f"✅ Unicode Test {i}: PASSED")
            passed += 1
        else:
            print(f"❌ Unicode Test {i}: FAILED")
            print(f"   Input: {input_text}")
            print(f"   Expected: {expected}")
            print(f"   Got: {result}")
            print()
    
    print(f"\n📊 Unicode Results: {passed}/{total} tests passed")
    return passed == total

def test_math_patterns():
    """Test xử lý các mẫu toán học"""
    print("\n🧪 Testing math patterns...")
    
    processor = MathFormulaProcessor()
    
    # Test các mẫu regex
    pattern_tests = [
        ("1/2", "1 chia 2"),
        ("√x", "căn bậc hai của x"),
        ("3√y", "3 căn bậc 3 của y"),
        ("x^2", "x mũ 2"),
        ("∫f(x)dx", "tích phân của f(x) theo x"),
    ]
    
    passed = 0
    total = len(pattern_tests)
    
    for i, (input_text, expected) in enumerate(pattern_tests, 1):
        result = processor.process_special_characters(input_text)
        success = result.strip() == expected.strip()
        
        if success:
            print(f"✅ Pattern Test {i}: PASSED")
            passed += 1
        else:
            print(f"❌ Pattern Test {i}: FAILED")
            print(f"   Input: {input_text}")
            print(f"   Expected: {expected}")
            print(f"   Got: {result}")
            print()
    
    print(f"\n📊 Pattern Results: {passed}/{total} tests passed")
    return passed == total

def test_text_cleaning():
    """Test làm sạch văn bản"""
    print("\n🧪 Testing text cleaning...")
    
    processor = MathFormulaProcessor()
    
    # Test cases
    cleaning_tests = [
        ("  x²  +  y³  ", "x mũ hai + y mũ ba"),
        ("( x + y )", "(x + y)"),
        ("x . y , z", "x. y, z"),
    ]
    
    passed = 0
    total = len(cleaning_tests)
    
    for i, (input_text, expected) in enumerate(cleaning_tests, 1):
        result = processor.process_special_characters(input_text)
        success = result.strip() == expected.strip()
        
        if success:
            print(f"✅ Cleaning Test {i}: PASSED")
            passed += 1
        else:
            print(f"❌ Cleaning Test {i}: FAILED")
            print(f"   Input: {input_text}")
            print(f"   Expected: {expected}")
            print(f"   Got: {result}")
            print()
    
    print(f"\n📊 Cleaning Results: {passed}/{total} tests passed")
    return passed == total

def test_utility_functions():
    """Test các hàm tiện ích"""
    print("\n🧪 Testing utility functions...")
    
    # Test process_math_text
    test_text = "x² + α = β"
    result = process_math_text(test_text)
    expected = "x mũ hai +  alpha =  beta"
    
    if result.strip() == expected.strip():
        print("✅ process_math_text: PASSED")
        utility_passed = True
    else:
        print("❌ process_math_text: FAILED")
        print(f"   Input: {test_text}")
        print(f"   Expected: {expected}")
        print(f"   Got: {result}")
        utility_passed = False
    
    return utility_passed

def main():
    """Main test function"""
    print("🚀 Starting MathFormulaProcessor tests...\n")
    
    tests = [
        test_special_characters,
        test_unicode_processing,
        test_math_patterns,
        test_text_cleaning,
        test_utility_functions,
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed_tests += 1
        except Exception as e:
            print(f"❌ Test {test_func.__name__} failed with error: {e}")
    
    print(f"\n🎯 Final Results: {passed_tests}/{total_tests} test suites passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! MathFormulaProcessor is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


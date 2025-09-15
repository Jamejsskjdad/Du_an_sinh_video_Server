#!/usr/bin/env python3
"""
Demo script cho MathFormulaProcessor
"""

import sys
import os

# Thêm đường dẫn src vào sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.math_formula_processor import MathFormulaProcessor, process_math_text

def main():
    """Demo chính"""
    print("🚀 MathFormulaProcessor Demo")
    print("=" * 50)
    
    processor = MathFormulaProcessor()
    
    # Test 1: Các ký tự đặc biệt cơ bản
    print("\n📝 Test 1: Ký tự đặc biệt cơ bản")
    test_cases = [
        "x² + y³ = z",
        "α + β = γ", 
        "H₂O",
        "πr²",
        "∑(i=1 to n) x_i"
    ]
    
    for text in test_cases:
        result = processor.process_special_characters(text)
        print(f"  {text} → {result}")
    
    # Test 2: Công thức toán học
    print("\n🔢 Test 2: Công thức toán học")
    math_cases = [
        "√x + ∫f(x)dx",
        "a/b × c",
        "3√y",
        "x^2 + y^3"
    ]
    
    for text in math_cases:
        result = processor.process_special_characters(text)
        print(f"  {text} → {result}")
    
    # Test 3: Công thức hóa học
    print("\n🧪 Test 3: Công thức hóa học")
    chem_cases = [
        "H₂SO₄",
        "CaCO₃",
        "Fe₂O₃",
        "C₆H₁₂O₆"
    ]
    
    for text in chem_cases:
        result = processor.process_special_characters(text)
        print(f"  {text} → {result}")
    
    # Test 4: Công thức vật lý
    print("\n⚡ Test 4: Công thức vật lý")
    physics_cases = [
        "E = mc²",
        "F = ma",
        "v = v₀ + at",
        "s = ut + ½at²"
    ]
    
    for text in physics_cases:
        result = processor.process_special_characters(text)
        print(f"  {text} → {result}")
    
    # Test 5: Debug một trường hợp cụ thể
    print("\n🔍 Test 5: Debug chi tiết")
    debug_text = "x² + α = β"
    debug_info = processor.debug_process(debug_text)
    print(f"  Input: {debug_text}")
    for step, result in debug_info.items():
        print(f"    {step}: {repr(result)}")
    
    print("\n✅ Demo hoàn thành!")
    return True

if __name__ == "__main__":
    main()


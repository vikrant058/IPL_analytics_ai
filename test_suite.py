"""
IPL Analytics AI Platform - Test & Validation Suite
=====================================================

Run this script to validate that all components are working correctly.
"""

import sys
import pandas as pd
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported"""
    print("\n📦 Testing Imports...")
    try:
        import pandas
        import numpy
        import fastapi
        import uvicorn
        import streamlit
        import plotly
        import sklearn
        import pydantic
        print("   ✅ All required libraries imported successfully")
        return True
    except ImportError as e:
        print(f"   ❌ Import Error: {e}")
        return False


def test_data_loading():
    """Test if data can be loaded properly"""
    print("\n📊 Testing Data Loading...")
    try:
        from data_loader import IPLDataLoader
        loader = IPLDataLoader()
        matches, deliveries = loader.load_data()
        
        if matches is not None and deliveries is not None:
            print(f"   ✅ Data loaded successfully")
            print(f"      - Matches: {len(matches)}")
            print(f"      - Deliveries: {len(deliveries)}")
            return True
        else:
            print("   ❌ Data loading returned None")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_preprocessing():
    """Test data preprocessing"""
    print("\n🔧 Testing Data Preprocessing...")
    try:
        from data_loader import IPLDataLoader
        loader = IPLDataLoader()
        matches, deliveries = loader.load_data()
        matches, deliveries = loader.preprocess_data()
        
        # Check if preprocessing worked
        if pd.api.types.is_datetime64_any_dtype(matches['date']):
            print("   ✅ Data preprocessing successful")
            return True
        else:
            print("   ❌ Date column not properly converted")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_stats_engine():
    """Test statistics engine"""
    print("\n📈 Testing Statistics Engine...")
    try:
        from data_loader import IPLDataLoader
        from stats_engine import StatsEngine
        
        loader = IPLDataLoader()
        matches, deliveries = loader.load_data()
        matches, deliveries = loader.preprocess_data()
        
        stats = StatsEngine(matches, deliveries)
        
        # Test player stats
        test_player = deliveries['batter'].iloc[0]
        player_stats = stats.get_player_stats(test_player)
        
        # Test team stats
        test_team = matches['team1'].iloc[0]
        team_stats = stats.get_team_stats(test_team)
        
        # Test top performers
        top_batsmen = stats.get_top_performers('batting', 5)
        top_bowlers = stats.get_top_performers('bowling', 5)
        
        if player_stats and team_stats and len(top_batsmen) > 0 and len(top_bowlers) > 0:
            print("   ✅ Statistics engine working correctly")
            return True
        else:
            print("   ❌ Some statistics calculations failed")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_ai_engine():
    """Test AI engine"""
    print("\n🤖 Testing AI Engine...")
    try:
        from data_loader import IPLDataLoader
        from ai_engine import AIEngine
        
        loader = IPLDataLoader()
        matches, deliveries = loader.load_data()
        matches, deliveries = loader.preprocess_data()
        
        ai = AIEngine(matches, deliveries)
        
        # Test predictions
        teams = set(list(matches['team1'].unique()) + list(matches['team2'].unique()))
        teams_list = list(teams)[:2]
        
        if len(teams_list) >= 2:
            prediction = ai.predict_match_winner(teams_list[0], teams_list[1])
            
            # Test H2H
            h2h = ai.get_head_to_head(teams_list[0], teams_list[1])
            
            # Test insights
            insights = ai.get_insights()
            
            if 'predicted_winner' in prediction and len(insights) > 0:
                print("   ✅ AI engine working correctly")
                return True
        
        print("   ❌ AI engine tests failed")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_models():
    """Test Pydantic models"""
    print("\n📋 Testing Pydantic Models...")
    try:
        from models import (
            PlayerStats, TeamStats, MatchPrediction, 
            APIResponse, BattingStats, BowlingStats
        )
        
        # Test creating model instances
        batting = BattingStats(
            matches=10, runs=500, balls=400, 
            average=50.0, strike_rate=125.0, highest_score=75
        )
        
        team = TeamStats(
            team="Mumbai Indians", matches=20, 
            wins=15, win_percentage=75.0
        )
        
        print("   ✅ Pydantic models validated successfully")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_api_models():
    """Test API endpoint availability"""
    print("\n🌐 Testing API Models...")
    try:
        from api import app
        print("   ✅ FastAPI app initialized successfully")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_streamlit_app():
    """Test Streamlit app imports"""
    print("\n🎨 Testing Streamlit App...")
    try:
        import streamlit as st
        print("   ✅ Streamlit app dependencies available")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def run_all_tests():
    """Run all validation tests"""
    print("\n" + "="*60)
    print("🧪 IPL Analytics AI Platform - Validation Suite")
    print("="*60)
    
    tests = [
        ("Imports", test_imports),
        ("Data Loading", test_data_loading),
        ("Data Preprocessing", test_preprocessing),
        ("Statistics Engine", test_stats_engine),
        ("AI Engine", test_ai_engine),
        ("Pydantic Models", test_models),
        ("API Models", test_api_models),
        ("Streamlit App", test_streamlit_app),
    ]
    
    results = {}
    for test_name, test_func in tests:
        results[test_name] = test_func()
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("\n" + "="*60)
    print(f"Results: {passed}/{total} tests passed")
    print("="*60)
    
    if passed == total:
        print("\n🎉 All tests passed! Platform is ready to use.")
        print("\nNext steps:")
        print("  1. Run Streamlit: streamlit run app.py")
        print("  2. Run FastAPI: python api.py")
        print("  3. View examples: python examples.py")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)

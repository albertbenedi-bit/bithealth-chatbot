import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open
from src.llm_abstraction.prompt_manager import PromptManager

class TestPromptManager:
    
    @pytest.fixture
    def temp_prompts_dir(self):
        """Create a temporary directory with test prompt files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            prompts_dir = Path(temp_dir) / "prompts"
            prompts_dir.mkdir()
            
            (prompts_dir / "greeting.txt").write_text("Hello! How can I help you today?")
            (prompts_dir / "appointment_booking.txt").write_text("I'll help you book an appointment. Please provide your preferred date: {date}")
            (prompts_dir / "emergency.txt").write_text("This is an emergency situation for patient {patient_name}. Immediate attention required.")
            
            yield prompts_dir
    
    def test_load_prompts_success(self, temp_prompts_dir):
        """Test successful loading of prompt files"""
        with patch.object(PromptManager, '__init__', lambda self, prompts_dir: setattr(self, 'prompts_dir', temp_prompts_dir) or setattr(self, 'prompts_cache', {}) or self._load_prompts()):
            manager = PromptManager(prompts_dir="prompts")
            
            assert len(manager.prompts_cache) == 3
            assert "greeting" in manager.prompts_cache
            assert "appointment_booking" in manager.prompts_cache
            assert "emergency" in manager.prompts_cache
            
            assert manager.prompts_cache["greeting"] == "Hello! How can I help you today?"
            assert "Please provide your preferred date: {date}" in manager.prompts_cache["appointment_booking"]
    
    def test_load_prompts_directory_not_exists(self):
        """Test handling when prompts directory doesn't exist"""
        with patch.object(Path, 'exists', return_value=False):
            manager = PromptManager(prompts_dir="nonexistent")
            
            assert len(manager.prompts_cache) == 0
    
    def test_get_prompt_without_variables(self, temp_prompts_dir):
        """Test getting prompt without variable substitution"""
        with patch.object(Path, '__new__', return_value=temp_prompts_dir.parent):
            manager = PromptManager(prompts_dir="prompts")
            
            prompt = manager.get_prompt("greeting")
            assert prompt == "Hello! How can I help you today?"
    
    def test_get_prompt_with_variables(self, temp_prompts_dir):
        """Test getting prompt with variable substitution"""
        with patch.object(Path, '__new__', return_value=temp_prompts_dir.parent):
            manager = PromptManager(prompts_dir="prompts")
            
            prompt = manager.get_prompt("appointment_booking", {"date": "2024-01-15"})
            assert "Please provide your preferred date: 2024-01-15" in prompt
    
    def test_get_prompt_with_multiple_variables(self, temp_prompts_dir):
        """Test getting prompt with multiple variables"""
        with patch.object(Path, '__new__', return_value=temp_prompts_dir.parent):
            manager = PromptManager(prompts_dir="prompts")
            
            prompt = manager.get_prompt("emergency", {
                "patient_name": "John Doe"
            })
            assert "emergency situation for patient John Doe" in prompt
    
    def test_get_prompt_not_found(self, temp_prompts_dir):
        """Test getting non-existent prompt"""
        with patch.object(Path, '__new__', return_value=temp_prompts_dir.parent):
            manager = PromptManager(prompts_dir="prompts")
            
            prompt = manager.get_prompt("nonexistent")
            assert "Prompt 'nonexistent' not found" in prompt
    
    def test_get_prompt_variable_substitution_error(self, temp_prompts_dir):
        """Test handling variable substitution errors"""
        with patch.object(Path, '__new__', return_value=temp_prompts_dir.parent):
            manager = PromptManager(prompts_dir="prompts")
            
            prompt = manager.get_prompt("appointment_booking", {"wrong_key": "value"})
            assert "Error loading prompt 'appointment_booking'" in prompt
    
    def test_list_prompts(self, temp_prompts_dir):
        """Test listing all available prompts"""
        with patch.object(Path, '__new__', return_value=temp_prompts_dir.parent):
            manager = PromptManager(prompts_dir="prompts")
            
            prompts = manager.list_prompts()
            assert len(prompts) == 3
            assert "greeting" in prompts
            assert "appointment_booking" in prompts
            assert "emergency" in prompts
    
    def test_reload_prompts(self, temp_prompts_dir):
        """Test reloading prompts"""
        with patch.object(Path, '__new__', return_value=temp_prompts_dir.parent):
            manager = PromptManager(prompts_dir="prompts")
            
            initial_count = len(manager.prompts_cache)
            assert initial_count == 3
            
            (temp_prompts_dir / "new_prompt.txt").write_text("This is a new prompt")
            
            manager.reload_prompts()
            
            assert len(manager.prompts_cache) == 4
            assert "new_prompt" in manager.prompts_cache
            assert manager.prompts_cache["new_prompt"] == "This is a new prompt"
    
    def test_load_prompts_with_encoding(self, temp_prompts_dir):
        """Test loading prompts with special characters"""
        special_prompt = "Selamat datang! Bagaimana saya bisa membantu Anda? 🏥"
        (temp_prompts_dir / "indonesian.txt").write_text(special_prompt, encoding='utf-8')
        
        with patch.object(Path, '__new__', return_value=temp_prompts_dir.parent):
            manager = PromptManager(prompts_dir="prompts")
            
            prompt = manager.get_prompt("indonesian")
            assert prompt == special_prompt
    
    def test_load_prompts_file_read_error(self):
        """Test handling file read errors"""
        with patch.object(Path, 'exists', return_value=True), \
             patch.object(Path, 'glob', return_value=[Path("test.txt")]), \
             patch('builtins.open', side_effect=IOError("Permission denied")):
            
            manager = PromptManager(prompts_dir="prompts")
            
            assert len(manager.prompts_cache) == 0
    
    def test_prompt_file_with_whitespace(self, temp_prompts_dir):
        """Test prompt files with leading/trailing whitespace"""
        prompt_with_whitespace = "  \n  This prompt has whitespace  \n  "
        (temp_prompts_dir / "whitespace.txt").write_text(prompt_with_whitespace)
        
        with patch.object(Path, '__new__', return_value=temp_prompts_dir.parent):
            manager = PromptManager(prompts_dir="prompts")
            
            prompt = manager.get_prompt("whitespace")
            assert prompt == "This prompt has whitespace"  # Should be stripped
    
    def test_empty_prompt_file(self, temp_prompts_dir):
        """Test handling empty prompt files"""
        (temp_prompts_dir / "empty.txt").write_text("")
        
        with patch.object(Path, '__new__', return_value=temp_prompts_dir.parent):
            manager = PromptManager(prompts_dir="prompts")
            
            prompt = manager.get_prompt("empty")
            assert prompt == ""
    
    def test_complex_variable_substitution(self, temp_prompts_dir):
        """Test complex variable substitution scenarios"""
        complex_prompt = """
        Patient: {patient_name}
        Appointment: {appointment_type} on {date} at {time}
        Doctor: {doctor_name}
        Location: {clinic_location}
        """
        (temp_prompts_dir / "complex.txt").write_text(complex_prompt)
        
        with patch.object(Path, '__new__', return_value=temp_prompts_dir.parent):
            manager = PromptManager(prompts_dir="prompts")
            
            variables = {
                "patient_name": "Jane Smith",
                "appointment_type": "Cardiology Consultation",
                "date": "2024-01-20",
                "time": "10:30 AM",
                "doctor_name": "Dr. Johnson",
                "clinic_location": "Building A, Floor 3"
            }
            
            prompt = manager.get_prompt("complex", variables)
            
            assert "Jane Smith" in prompt
            assert "Cardiology Consultation" in prompt
            assert "2024-01-20" in prompt
            assert "10:30 AM" in prompt
            assert "Dr. Johnson" in prompt
            assert "Building A, Floor 3" in prompt

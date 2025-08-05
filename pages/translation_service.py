# pages/translation_service.py

from googletrans import Translator
import logging

logger = logging.getLogger(__name__)

class TranslationService:
    """Service for translating text to Greek"""
    
    def __init__(self):
        self.translator = Translator()
    
    def translate_to_greek(self, text):
        """
        Translate English text to Greek
        Returns the translated text or the original text if translation fails
        """
        if not text or not text.strip():
            return text
            
        try:
            # Detect if text is already in Greek
            detection = self.translator.detect(text)
            if detection.lang == 'el':  # Greek language code
                return text
                
            # Translate to Greek
            result = self.translator.translate(text, src='en', dest='el')
            translated_text = result.text
            
            logger.info(f"Translated '{text}' to '{translated_text}'")
            return translated_text
            
        except Exception as e:
            logger.error(f"Translation failed for '{text}': {str(e)}")
            # Return original text if translation fails
            return text
    
    def ensure_greek_translations(self, project):
        """
        Ensure a project and its tasks have Greek translations
        """
        try:
            updated = False
            
            # Translate project name
            if not project.project_name_greek and project.project_name:
                project.project_name_greek = self.translate_to_greek(project.project_name)
                updated = True
            
            # Translate project description
            if not project.project_description_greek and project.project_description:
                project.project_description_greek = self.translate_to_greek(project.project_description)
                updated = True
            
            if updated:
                project.save()
            
            # Translate tasks and subtasks
            tasks = project.projecttask_set.all()
            for task in tasks:
                task_updated = False
                
                # Translate task name
                if not task.task_name_greek and task.task_name:
                    task.task_name_greek = self.translate_to_greek(task.task_name)
                    task_updated = True
                
                # Translate task description
                if not task.task_description_greek and task.task_description:
                    task.task_description_greek = self.translate_to_greek(task.task_description)
                    task_updated = True
                
                if task_updated:
                    task.save()
            
            logger.info(f"Greek translations ensured for project: {project.project_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error ensuring Greek translations for project {project.project_id}: {str(e)}")
            return False


# Global instance
translation_service = TranslationService()


# Utility functions for use in views
def get_translated_text(english_text, greek_text, language='english'):
    """
    Return appropriate text based on language preference
    """
    if language == 'greek' and greek_text:
        return greek_text
    elif language == 'greek' and not greek_text and english_text:
        # Auto-translate if Greek version doesn't exist
        try:
            return translation_service.translate_to_greek(english_text)
        except:
            return english_text
    else:
        return english_text or ''


def ensure_project_translations(project):
    """
    Ensure a project has Greek translations (used in views)
    """
    return translation_service.ensure_greek_translations(project)
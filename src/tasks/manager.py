import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import uuid


@dataclass
class TaskItem:
    """Task/Todo item data structure"""
    id: str
    title: str
    description: str
    status: str  # "pending", "in_progress", "completed", "cancelled"
    priority: str  # "low", "medium", "high", "urgent"
    created_at: datetime
    updated_at: datetime
    due_date: Optional[datetime] = None
    source: str = "voice_command"  # "voice_command", "manual", "jira", etc.
    context: Optional[str] = None  # Original context from voice
    confidence: float = 0.0
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
            
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        if self.due_date:
            data['due_date'] = self.due_date.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TaskItem':
        """Create TaskItem from dictionary"""
        # Convert ISO strings back to datetime objects
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        if data.get('due_date'):
            data['due_date'] = datetime.fromisoformat(data['due_date'])
        return cls(**data)


class TaskManager:
    """
    Manage tasks extracted from voice commands and other sources
    """
    
    def __init__(self, db_path: str = "tasks.db"):
        self.db_path = db_path
        self._init_database()
        
    def _init_database(self):
        """Initialize SQLite database for task storage"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    priority TEXT NOT NULL DEFAULT 'medium',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    due_date TEXT,
                    source TEXT NOT NULL DEFAULT 'voice_command',
                    context TEXT,
                    confidence REAL DEFAULT 0.0,
                    tags TEXT  -- JSON array
                )
            """)
            
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON tasks(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON tasks(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_priority ON tasks(priority)")
            
    def create_task(self, 
                   title: str,
                   description: str = "",
                   priority: str = "medium",
                   due_date: Optional[datetime] = None,
                   source: str = "voice_command",
                   context: str = "",
                   confidence: float = 0.0,
                   tags: List[str] = None) -> TaskItem:
        """Create a new task"""
        
        task = TaskItem(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            status="pending",
            priority=priority,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            due_date=due_date,
            source=source,
            context=context,
            confidence=confidence,
            tags=tags or []
        )
        
        self._save_task(task)
        return task
        
    def _save_task(self, task: TaskItem):
        """Save task to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO tasks 
                (id, title, description, status, priority, created_at, updated_at, 
                 due_date, source, context, confidence, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.id,
                task.title,
                task.description,
                task.status,
                task.priority,
                task.created_at.isoformat(),
                task.updated_at.isoformat(),
                task.due_date.isoformat() if task.due_date else None,
                task.source,
                task.context,
                task.confidence,
                json.dumps(task.tags)
            ))
            
    def get_task(self, task_id: str) -> Optional[TaskItem]:
        """Get task by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            
            if row:
                return self._row_to_task(row)
        return None
        
    def get_tasks(self, 
                  status: Optional[str] = None,
                  priority: Optional[str] = None,
                  limit: int = 100) -> List[TaskItem]:
        """Get tasks with optional filtering"""
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
            
        if priority:
            query += " AND priority = ?"
            params.append(priority)
            
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            return [self._row_to_task(row) for row in rows]
            
    def update_task_status(self, task_id: str, status: str) -> bool:
        """Update task status"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                UPDATE tasks 
                SET status = ?, updated_at = ?
                WHERE id = ?
            """, (status, datetime.now().isoformat(), task_id))
            
            return cursor.rowcount > 0
            
    def delete_task(self, task_id: str) -> bool:
        """Delete task"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            return cursor.rowcount > 0
            
    def _row_to_task(self, row: sqlite3.Row) -> TaskItem:
        """Convert database row to TaskItem"""
        return TaskItem(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            status=row["status"],
            priority=row["priority"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            due_date=datetime.fromisoformat(row["due_date"]) if row["due_date"] else None,
            source=row["source"],
            context=row["context"],
            confidence=row["confidence"],
            tags=json.loads(row["tags"]) if row["tags"] else []
        )
        
    def get_pending_tasks_count(self) -> int:
        """Get count of pending tasks"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM tasks WHERE status = 'pending'")
            return cursor.fetchone()[0]
            
    def get_tasks_summary(self) -> Dict[str, int]:
        """Get summary of tasks by status"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT status, COUNT(*) as count 
                FROM tasks 
                GROUP BY status
            """)
            
            return {row[0]: row[1] for row in cursor.fetchall()}


class VoiceTaskProcessor:
    """
    Process voice commands and create tasks from extracted content
    """
    
    def __init__(self, task_manager: TaskManager):
        self.task_manager = task_manager
        
    def process_voice_command(self, command_data: Dict) -> List[TaskItem]:
        """Process voice command and create tasks"""
        created_tasks = []
        
        # Extract context text
        context_text = command_data.get("context_text", "")
        if not context_text:
            return created_tasks
            
        # Simple task extraction - look for action items
        potential_tasks = self._extract_action_items(context_text)
        
        for task_text in potential_tasks:
            # Create task from extracted text
            task = self.task_manager.create_task(
                title=self._generate_task_title(task_text),
                description=task_text,
                source="voice_command",
                context=context_text,
                confidence=0.8,  # Default confidence
                tags=["voice_generated", "auto_extracted"]
            )
            created_tasks.append(task)
            
        return created_tasks
        
    def _extract_action_items(self, text: str) -> List[str]:
        """Extract potential action items from text"""
        import re
        
        # Split text into sentences
        sentences = re.split(r'[。．.!！？\?]', text)
        action_items = []
        
        # Keywords that indicate action items
        action_keywords = [
            r'する$', r'やる$', r'確認する$', r'調べる$', r'連絡する$',
            r'作成する$', r'修正する$', r'対応する$', r'準備する$',
            r'送る$', r'書く$', r'読む$', r'考える$', r'検討する$'
        ]
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 5:  # Skip very short sentences
                continue
                
            # Check if sentence contains action keywords
            for keyword in action_keywords:
                if re.search(keyword, sentence):
                    action_items.append(sentence)
                    break
                    
        return action_items
        
    def _generate_task_title(self, text: str) -> str:
        """Generate concise task title from text"""
        # Take first 50 characters and add ellipsis if needed
        title = text[:50].strip()
        if len(text) > 50:
            title += "..."
        return title


# Jira integration placeholder for future implementation
class JiraIntegration:
    """
    Future: Integration with Jira for task management
    """
    
    def __init__(self, jira_url: str, username: str, api_token: str):
        self.jira_url = jira_url
        self.username = username
        self.api_token = api_token
        
    def create_jira_task(self, task: TaskItem) -> str:
        """Create task in Jira and return issue key"""
        # Implementation would use jira library or REST API
        pass
        
    def sync_task_status(self, task_id: str, jira_key: str):
        """Sync task status between local and Jira"""
        pass
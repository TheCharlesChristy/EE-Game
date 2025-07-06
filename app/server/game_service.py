"""
Game Service - All Game Logic for Multi-Team Gaming System
Handles Reaction Timer, Wheel Game, and Quiz Game logic
"""

import time
import random
import threading
from typing import Dict, List, Optional


class GameService:
    """Simple game service handling all three games."""
    
    def __init__(self, gpio_service, websocket_service):
        self.gpio = gpio_service
        self.websocket = websocket_service
        self.game_state = {}
        self.current_game = None
        self.game_thread = None
    
    # Reaction Timer Game
    def start_reaction_timer(self, team_ids: List[int]) -> Dict:
        """Start a reaction timer game."""
        if self.current_game:
            return {"status": "error", "message": "Game already in progress"}
        
        self.current_game = "reaction_timer"
        self.game_state = {
            'game_id': 'reaction_timer',
            'teams': {tid: {'lives': 3, 'eliminated': False} for tid in team_ids},
            'round': 0,
            'max_rounds': 20,
            'time_limit_ms': 200,
            'status': 'active'
        }
        
        # Broadcast game start
        self.websocket.broadcast_game_started('reaction_timer', team_ids)
        
        # Start game in background thread
        self.game_thread = threading.Thread(target=self.run_reaction_timer, daemon=True)
        self.game_thread.start()
        
        return {"status": "success", "game_id": "reaction_timer"}
    
    def run_reaction_timer(self):
        """Main reaction timer game loop."""
        while (self.current_game == "reaction_timer" and 
               self.game_state['round'] < self.game_state['max_rounds']):
            
            active_teams = [tid for tid, data in self.game_state['teams'].items() 
                           if not data['eliminated']]
            
            if len(active_teams) <= 1:
                break  # Game over
            
            self.start_reaction_round(active_teams)
            time.sleep(2)  # Pause between rounds
        
        self.end_reaction_timer()
    
    def start_reaction_round(self, active_teams: List[int]):
        """Start a single reaction timer round."""
        self.game_state['round'] += 1
        
        # Calculate time limit (gets shorter each round)
        base_time = 200
        time_reduction = self.game_state['round'] * 5
        time_limit = max(50, base_time - time_reduction)
        self.game_state['time_limit_ms'] = time_limit
        
        # Broadcast round start
        self.websocket.broadcast_round_started(
            self.game_state['round'], 
            time_limit, 
            active_teams
        )
        
        # Emit screen state change to red
        self.websocket.socketio.emit('screen_state_change', {'state': 'red'})
        self.websocket.socketio.emit('game_phase_update', {'phase': 'preparing'})
        
        # Wait random delay (2-8 seconds)
        delay = random.uniform(2.0, 8.0)
        time.sleep(delay)
        
        # Turn on all LEDs (green screen moment)
        for team_id in active_teams:
            self.gpio.control_led(team_id, True)
        
        # Emit screen state change to green and LED status
        self.websocket.socketio.emit('screen_state_change', {'state': 'green'})
        self.websocket.socketio.emit('game_phase_update', {'phase': 'active'})
        self.websocket.socketio.emit('led_status_update', {
            'teams': [{'team_id': tid, 'led_status': 'on'} for tid in active_teams]
        })
        
        start_time = time.time()
        button_presses = []
        
        # Collect button presses for time limit
        while time.time() - start_time < (time_limit / 1000.0):
            events = self.gpio.get_button_events()
            for event in events:
                if event['team_id'] in active_teams:
                    reaction_time = (event['timestamp'] - start_time) * 1000
                    button_presses.append({
                        'team_id': event['team_id'],
                        'reaction_time': reaction_time,
                        'valid': True
                    })
                    # Broadcast button press
                    self.websocket.broadcast_button_press(
                        event['team_id'], 
                        event['timestamp'], 
                        reaction_time, 
                        True
                    )
            time.sleep(0.001)
        
        # Turn off all LEDs
        for team_id in active_teams:
            self.gpio.control_led(team_id, False)
        
        # Emit LED status update and screen state
        self.websocket.socketio.emit('led_status_update', {
            'teams': [{'team_id': tid, 'led_status': 'off'} for tid in active_teams]
        })
        self.websocket.socketio.emit('screen_state_change', {'state': 'waiting'})
        self.websocket.socketio.emit('game_phase_update', {'phase': 'complete'})
        
        # Process results
        self.process_reaction_results(active_teams, button_presses)
    
    def process_reaction_results(self, active_teams: List[int], button_presses: List[Dict]):
        """Process reaction timer round results."""
        pressed_teams = {press['team_id'] for press in button_presses}
        
        round_results = []
        
        # Teams that didn't press lose a life
        for team_id in active_teams:
            if team_id not in pressed_teams:
                self.game_state['teams'][team_id]['lives'] -= 1
                if self.game_state['teams'][team_id]['lives'] <= 0:
                    self.game_state['teams'][team_id]['eliminated'] = True
                
                round_results.append({
                    'team_id': team_id,
                    'pressed': False,
                    'eliminated': self.game_state['teams'][team_id]['eliminated'],
                    'lives': self.game_state['teams'][team_id]['lives']
                })
            else:
                # Find the button press for this team
                press_data = next((p for p in button_presses if p['team_id'] == team_id), None)
                round_results.append({
                    'team_id': team_id,
                    'pressed': True,
                    'reaction_time': press_data['reaction_time'] if press_data else None,
                    'eliminated': False,
                    'lives': self.game_state['teams'][team_id]['lives']
                })
        
        # Broadcast round results
        self.websocket.socketio.emit('round_complete', {
            'round': self.game_state['round'],
            'results': round_results,
            'eliminated_teams': [r['team_id'] for r in round_results if r['eliminated']]
        })
        
        # Update team status
        self.websocket.socketio.emit('team_status_update', {
            'teams': [
                {
                    'team_id': team_id,
                    'lives': data['lives'],
                    'eliminated': data['eliminated']
                }
                for team_id, data in self.game_state['teams'].items()
            ]
        })
    
    def end_reaction_timer(self):
        """End the reaction timer game."""
        # Find winner
        active_teams = [(tid, data) for tid, data in self.game_state['teams'].items() 
                       if not data['eliminated']]
        
        if active_teams:
            winner_id = active_teams[0][0]
            from .data_service import data_service
            winner_team = data_service.get_team_by_id(winner_id)
            winner_data = {"team_id": winner_id, "team_name": winner_team['name']}
        else:
            winner_data = None
        
        # Broadcast game end
        self.websocket.socketio.emit('game_ended', {
            'winner': winner_data,
            'final_standings': self.get_final_standings(),
            'game_stats': self.get_game_statistics()
        })
        
        if winner_data:
            self.websocket.socketio.emit('winner_announced', {
                'winner': winner_data
            })
        
        # Clean up
        self.current_game = None
        self.game_state = {}
    
    def stop_current_game(self):
        """Stop the currently running game."""
        if self.current_game:
            self.current_game = None
            if self.game_thread and self.game_thread.is_alive():
                # Game thread will exit on next iteration
                pass
            
            # Turn off all LEDs
            self.gpio.reset_all_leds()
            
            # Emit stop events
            self.websocket.socketio.emit('game_state_change', {'state': 'stopped'})
            self.websocket.socketio.emit('screen_state_change', {'state': 'waiting'})
            
            return {"status": "success", "message": "Game stopped"}
        else:
            return {"status": "error", "message": "No game currently running"}
    
    def reset_game(self):
        """Reset the current game state."""
        self.stop_current_game()
        
        # Reset GPIO
        self.gpio.reset_all_leds()
        
        # Clear game state
        self.game_state = {}
        
        # Emit reset events
        self.websocket.socketio.emit('game_state_change', {'state': 'waiting'})
        self.websocket.socketio.emit('screen_state_change', {'state': 'waiting'})
        
        return {"status": "success", "message": "Game reset"}
    
    def abort_game(self):
        """Emergency abort the current game."""
        result = self.stop_current_game()
        
        # Emit abort event
        self.websocket.socketio.emit('game_state_change', {'state': 'aborted'})
        self.websocket.socketio.emit('error_occurred', {
            'message': 'Game aborted by operator',
            'type': 'abort'
        })
        
        return result
    
    def get_final_standings(self):
        """Get final game standings."""
        if not self.game_state or 'teams' not in self.game_state:
            return []
        
        teams = []
        for team_id, data in self.game_state['teams'].items():
            from .data_service import data_service
            team_info = data_service.get_team_by_id(team_id)
            teams.append({
                'team_id': team_id,
                'team_name': team_info['name'] if team_info else f'Team {team_id}',
                'lives': data['lives'],
                'eliminated': data['eliminated'],
                'rounds_survived': self.game_state['round'] if not data['eliminated'] else 
                                 self.game_state['round'] - 1
            })
        
        # Sort by elimination status and lives remaining
        teams.sort(key=lambda x: (x['eliminated'], -x['lives'], -x['rounds_survived']))
        return teams
    
    def get_game_statistics(self):
        """Get game statistics."""
        if not self.game_state:
            return {}
        
        return {
            'total_rounds': self.game_state.get('round', 0),
            'teams_eliminated': len([t for t in self.game_state.get('teams', {}).values() 
                                   if t.get('eliminated')]),
            'average_time': self.game_state.get('time_limit_ms', 200),
            'game_duration': time.time() - self.game_state.get('start_time', time.time())
        }
    
    # Wheel Game
    def start_wheel_game(self, team_ids: List[int]) -> Dict:
        """Start a wheel game."""
        if self.current_game:
            return {"status": "error", "message": "Game already in progress"}
        
        self.current_game = "wheel_game"
        self.game_state = {
            'game_id': 'wheel_game',
            'teams': {tid: {'score': 0} for tid in team_ids},
            'round': 0,
            'total_rounds': 10,
            'status': 'active'
        }
        
        # Broadcast game start
        self.websocket.broadcast_game_started('wheel_game', team_ids)
        
        # Start game in background thread
        self.game_thread = threading.Thread(target=self.run_wheel_game, daemon=True)
        self.game_thread.start()
        
        return {"status": "success", "game_id": "wheel_game"}
    
    def run_wheel_game(self):
        """Main wheel game loop."""
        modes = ['one_vs_one', 'free_for_all', 'red_vs_blue']
        
        while (self.current_game == "wheel_game" and 
               self.game_state['round'] < self.game_state['total_rounds']):
            
            self.game_state['round'] += 1
            mode = random.choice(modes)
            
            self.websocket.broadcast_round_started(
                self.game_state['round'], 
                0,  # No time limit for wheel game
                list(self.game_state['teams'].keys())
            )
            
            if mode == 'one_vs_one':
                self.execute_1v1()
            elif mode == 'free_for_all':
                self.execute_free_for_all()
            elif mode == 'red_vs_blue':
                self.execute_red_vs_blue()
            
            time.sleep(3)  # Pause between rounds
        
        self.end_wheel_game()
    
    def execute_1v1(self):
        """Execute one vs one wheel game mode."""
        team_ids = list(self.game_state['teams'].keys())
        if len(team_ids) < 2:
            return
        
        # Pick two random teams
        competitors = random.sample(team_ids, 2)
        
        # Light up their LEDs
        for team_id in competitors:
            self.gpio.control_led(team_id, True)
        
        # Wait for first button press
        start_time = time.time()
        while time.time() - start_time < 10.0:  # 10 second timeout
            events = self.gpio.get_button_events()
            for event in events:
                if event['team_id'] in competitors:
                    # Winner gets a point
                    self.game_state['teams'][event['team_id']]['score'] += 1
                    
                    # Turn off LEDs
                    for team_id in competitors:
                        self.gpio.control_led(team_id, False)
                    
                    return
            time.sleep(0.01)
        
        # Timeout - turn off LEDs
        for team_id in competitors:
            self.gpio.control_led(team_id, False)
    
    def execute_free_for_all(self):
        """Execute free for all wheel game mode."""
        team_ids = list(self.game_state['teams'].keys())
        
        # Light up all LEDs
        for team_id in team_ids:
            self.gpio.control_led(team_id, True)
        
        # Wait for first button press
        start_time = time.time()
        while time.time() - start_time < 10.0:  # 10 second timeout
            events = self.gpio.get_button_events()
            for event in events:
                if event['team_id'] in team_ids:
                    # Winner gets a point
                    self.game_state['teams'][event['team_id']]['score'] += 2
                    
                    # Turn off LEDs
                    for team_id in team_ids:
                        self.gpio.control_led(team_id, False)
                    
                    return
            time.sleep(0.01)
        
        # Timeout - turn off LEDs
        for team_id in team_ids:
            self.gpio.control_led(team_id, False)
    
    def execute_red_vs_blue(self):
        """Execute red vs blue wheel game mode."""
        team_ids = list(self.game_state['teams'].keys())
        if len(team_ids) < 2:
            return
        
        # Split teams into two groups
        mid = len(team_ids) // 2
        red_teams = team_ids[:mid]
        blue_teams = team_ids[mid:]
        
        # Light up all LEDs
        for team_id in team_ids:
            self.gpio.control_led(team_id, True)
        
        # Wait for first button press
        start_time = time.time()
        while time.time() - start_time < 10.0:  # 10 second timeout
            events = self.gpio.get_button_events()
            for event in events:
                team_id = event['team_id']
                if team_id in red_teams:
                    # Red team wins - all red teams get points
                    for red_team in red_teams:
                        self.game_state['teams'][red_team]['score'] += 1
                elif team_id in blue_teams:
                    # Blue team wins - all blue teams get points
                    for blue_team in blue_teams:
                        self.game_state['teams'][blue_team]['score'] += 1
                
                # Turn off LEDs
                for tid in team_ids:
                    self.gpio.control_led(tid, False)
                
                return
            time.sleep(0.01)
        
        # Timeout - turn off LEDs
        for team_id in team_ids:
            self.gpio.control_led(team_id, False)
    
    def end_wheel_game(self):
        """End the wheel game."""
        # Sort teams by score
        sorted_teams = sorted(
            self.game_state['teams'].items(), 
            key=lambda x: x[1]['score'], 
            reverse=True
        )
        
        if sorted_teams:
            winner_id = sorted_teams[0][0]
            from .data_service import data_service
            winner_team = data_service.get_team_by_id(winner_id)
            winner_data = {"team_id": winner_id, "team_name": winner_team['name']}
        else:
            winner_data = None
        
        # Create final standings
        final_standings = []
        for i, (team_id, team_data) in enumerate(sorted_teams):
            from .data_service import data_service
            team = data_service.get_team_by_id(team_id)
            final_standings.append({
                "team_id": team_id,
                "team_name": team['name'],
                "position": i + 1,
                "score": team_data['score']
            })
        
        # Broadcast game end
        self.websocket.broadcast_game_ended(winner_data, final_standings)
        
        # Reset game state
        self.current_game = None
        self.game_state = {}
    
    # Quiz Game
    def start_quiz_game(self, team_ids: List[int]) -> Dict:
        """Start a quiz game."""
        if self.current_game:
            return {"status": "error", "message": "Game already in progress"}
        
        from .data_service import data_service
        questions = data_service.get_questions()
        if not questions:
            return {"status": "error", "message": "No questions available"}
        
        self.current_game = "quiz_game"
        self.game_state = {
            'game_id': 'quiz_game',
            'teams': {tid: {'score': 0, 'locked_out': False} for tid in team_ids},
            'question_active': False,
            'current_question': None,
            'questions_asked': 0,
            'max_questions': min(10, len(questions)),
            'status': 'active'
        }
        
        # Broadcast game start
        self.websocket.broadcast_game_started('quiz_game', team_ids)
        
        # Start game in background thread
        self.game_thread = threading.Thread(target=self.run_quiz_game, daemon=True)
        self.game_thread.start()
        
        return {"status": "success", "game_id": "quiz_game"}
    
    def run_quiz_game(self):
        """Main quiz game loop."""
        from .data_service import data_service
        
        while (self.current_game == "quiz_game" and 
               self.game_state['questions_asked'] < self.game_state['max_questions']):
            
            # Get random question
            question = data_service.get_random_question()
            if not question:
                break
            
            self.present_question(question)
            time.sleep(5)  # Time to answer
            self.process_question_results()
            time.sleep(2)  # Pause between questions
        
        self.end_quiz_game()
    
    def present_question(self, question: Dict):
        """Present a quiz question."""
        self.game_state['current_question'] = question
        self.game_state['question_active'] = True
        self.game_state['questions_asked'] += 1
        
        # Reset lockouts
        for team_id in self.game_state['teams']:
            self.game_state['teams'][team_id]['locked_out'] = False
        
        # Light up all LEDs to indicate question is active
        for team_id in self.game_state['teams']:
            self.gpio.control_led(team_id, True)
        
        # Broadcast question (in real implementation, this would go to display)
        self.websocket.socketio.emit('quiz_question', {
            'question': question['question'],
            'round': self.game_state['questions_asked']
        })
    
    def process_question_results(self):
        """Process quiz question results."""
        self.game_state['question_active'] = False
        
        # Turn off all LEDs
        for team_id in self.game_state['teams']:
            self.gpio.control_led(team_id, False)
        
        # Check for button presses during question time
        events = self.gpio.get_button_events()
        first_buzzer = None
        
        for event in events:
            team_id = event['team_id']
            if (team_id in self.game_state['teams'] and 
                not self.game_state['teams'][team_id]['locked_out']):
                first_buzzer = team_id
                break
        
        if first_buzzer:
            # In a real implementation, this would prompt for an answer
            # For now, randomly award points
            if random.choice([True, False]):  # 50% chance of correct answer
                points = self.game_state['current_question'].get('points', 10)
                self.game_state['teams'][first_buzzer]['score'] += points
    
    def end_quiz_game(self):
        """End the quiz game."""
        # Sort teams by score
        sorted_teams = sorted(
            self.game_state['teams'].items(), 
            key=lambda x: x[1]['score'], 
            reverse=True
        )
        
        if sorted_teams:
            winner_id = sorted_teams[0][0]
            from .data_service import data_service
            winner_team = data_service.get_team_by_id(winner_id)
            winner_data = {"team_id": winner_id, "team_name": winner_team['name']}
        else:
            winner_data = None
        
        # Create final standings
        final_standings = []
        for i, (team_id, team_data) in enumerate(sorted_teams):
            from .data_service import data_service
            team = data_service.get_team_by_id(team_id)
            final_standings.append({
                "team_id": team_id,
                "team_name": team['name'],
                "position": i + 1,
                "score": team_data['score']
            })
        
        # Broadcast game end
        self.websocket.broadcast_game_ended(winner_data, final_standings)
        
        # Reset game state
        self.current_game = None
        self.game_state = {}
    
    # General game methods
    def get_available_games(self) -> List[Dict]:
        """Get list of available games."""
        from .data_service import data_service
        
        games = []
        
        if data_service.is_game_enabled('reaction_timer'):
            games.append({
                'id': 'reaction_timer',
                'name': 'Reaction Timer',
                'min_teams': 2,
                'status': 'available' if not self.current_game else 'unavailable'
            })
        
        if data_service.is_game_enabled('wheel_game'):
            games.append({
                'id': 'wheel_game',
                'name': 'Wheel Game',
                'min_teams': 2,
                'status': 'available' if not self.current_game else 'unavailable'
            })
        
        if data_service.is_game_enabled('quiz_game'):
            games.append({
                'id': 'quiz_game',
                'name': 'Quiz Game',
                'min_teams': 2,
                'status': 'available' if not self.current_game else 'unavailable'
            })
        
        return games
    
    def validate_game_start(self, game_id: str, team_count: int) -> Dict:
        """Validate if a game can be started."""
        if self.current_game:
            return {"can_start": False, "issues": ["Game already in progress"]}
        
        issues = []
        
        # Check minimum teams
        if team_count < 2:
            issues.append("At least 2 teams required")
        
        # Check game-specific requirements
        from .data_service import data_service
        if not data_service.is_game_enabled(game_id):
            issues.append(f"Game {game_id} is not enabled")
        
        if game_id == 'quiz_game':
            questions = data_service.get_questions()
            if not questions:
                issues.append("No quiz questions available")
        
        return {"can_start": len(issues) == 0, "issues": issues}
    
    def stop_current_game(self):
        """Stop the currently running game."""
        if self.current_game:
            self.current_game = None
            if self.game_thread and self.game_thread.is_alive():
                # Game thread will exit on next iteration
                pass
            
            # Turn off all LEDs
            self.gpio.reset_all_leds()
            
            # Emit stop events
            self.websocket.socketio.emit('game_state_change', {'state': 'stopped'})
            self.websocket.socketio.emit('screen_state_change', {'state': 'waiting'})
            
            return {"status": "success", "message": "Game stopped"}
        else:
            return {"status": "error", "message": "No game currently running"}
    
    def reset_game(self):
        """Reset the current game state."""
        self.stop_current_game()
        
        # Reset GPIO
        self.gpio.reset_all_leds()
        
        # Clear game state
        self.game_state = {}
        
        # Emit reset events
        self.websocket.socketio.emit('game_state_change', {'state': 'waiting'})
        self.websocket.socketio.emit('screen_state_change', {'state': 'waiting'})
        
        return {"status": "success", "message": "Game reset"}
    
    def abort_game(self):
        """Emergency abort the current game."""
        result = self.stop_current_game()
        
        # Emit abort event
        self.websocket.socketio.emit('game_state_change', {'state': 'aborted'})
        self.websocket.socketio.emit('error_occurred', {
            'message': 'Game aborted by operator',
            'type': 'abort'
        })
        
        return result
    
    def get_final_standings(self):
        """Get final game standings."""
        if not self.game_state or 'teams' not in self.game_state:
            return []
        
        teams = []
        for team_id, data in self.game_state['teams'].items():
            from .data_service import data_service
            team_info = data_service.get_team_by_id(team_id)
            teams.append({
                'team_id': team_id,
                'team_name': team_info['name'] if team_info else f'Team {team_id}',
                'lives': data['lives'],
                'eliminated': data['eliminated'],
                'rounds_survived': self.game_state['round'] if not data['eliminated'] else 
                                 self.game_state['round'] - 1
            })
        
        # Sort by elimination status and lives remaining
        teams.sort(key=lambda x: (x['eliminated'], -x['lives'], -x['rounds_survived']))
        return teams
    
    def get_game_statistics(self):
        """Get game statistics."""
        if not self.game_state:
            return {}
        
        return {
            'total_rounds': self.game_state.get('round', 0),
            'teams_eliminated': len([t for t in self.game_state.get('teams', {}).values() 
                                   if t.get('eliminated')]),
            'average_time': self.game_state.get('time_limit_ms', 200),
            'game_duration': time.time() - self.game_state.get('start_time', time.time())
        }

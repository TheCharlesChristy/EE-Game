import logging
from flask_socketio import emit
from EEGame.app.server.services.team_manager import TeamManager
from EEGame.app.server.EElogging import setup_logging
from EEGame.app.server.socketio.socketio_emitter import SocketIOEmitter

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)

def create_team_endpoints(app, socketio, team_manager: TeamManager, emitter: SocketIOEmitter):
    """
    Create SocketIO endpoints for team management and interaction.
    
    Args:
        app: Flask application instance
        socketio: SocketIO instance
        team_manager: TeamManager instance for team operations
        emitter: SocketIOEmitter instance for handling emissions
    """

    @socketio.on('create_team')
    def handle_create_team(data):
        """Create a new team."""
        try:
            team_id = data.get('team_id')
            name = data.get('name')
            team_color = data.get('team_color')
            latch_pin = data.get('latch_pin')
            reset_pin = data.get('reset_pin')
            led_pin = data.get('led_pin')

            # Validate required fields
            if not all([team_id, name, team_color, latch_pin, reset_pin, led_pin]):
                emitter.emit_team_error('All fields are required')
                return

            # Create the team
            team = team_manager.create_team(team_id, name, team_color, latch_pin, reset_pin, led_pin)
            
            logger.info(f"Team created: {team_id}")
            emitter.emit_team_created(team.to_dict())
            
            # Broadcast to all clients that a new team was created
            emitter.broadcast_team_list_updated([t.to_dict() for t in team_manager.get_all_teams().values()])

        except ValueError as e:
            logger.error(f"Error creating team: {str(e)}")
            emitter.emit_team_error(str(e))
        except Exception as e:
            logger.error(f"Unexpected error creating team: {str(e)}")
            emitter.emit_team_error('Failed to create team')

    @socketio.on('update_team')
    def handle_update_team(data):
        """Update an existing team."""
        try:
            team_id = data.get('team_id')
            if not team_id:
                emitter.emit_team_error('Team ID is required')
                return

            # Extract optional update fields
            update_data = {
                'name': data.get('name'),
                'team_color': data.get('team_color'),
                'latch_pin': data.get('latch_pin'),
                'reset_pin': data.get('reset_pin'),
                'led_pin': data.get('led_pin')
            }
            
            # Remove None values
            update_data = {k: v for k, v in update_data.items() if v is not None}

            # Update the team
            team = team_manager.update_team(team_id, **update_data)
            
            logger.info(f"Team updated: {team_id}")
            emitter.emit_team_updated(team.to_dict())
            
            # Broadcast to all clients that a team was updated
            emitter.broadcast_team_list_updated([t.to_dict() for t in team_manager.get_all_teams().values()])

        except ValueError as e:
            logger.error(f"Error updating team: {str(e)}")
            emitter.emit_team_error(str(e))
        except Exception as e:
            logger.error(f"Unexpected error updating team: {str(e)}")
            emitter.emit_team_error('Failed to update team')

    @socketio.on('delete_team')
    def handle_delete_team(data):
        """Delete a team."""
        try:
            team_id = data.get('team_id')
            if not team_id:
                emitter.emit_team_error('Team ID is required')
                return

            # Remove the team
            team_manager.remove_team(team_id)
            
            logger.info(f"Team deleted: {team_id}")
            emitter.emit_team_deleted(team_id)
            
            # Broadcast to all clients that a team was deleted
            emitter.broadcast_team_list_updated([t.to_dict() for t in team_manager.get_all_teams().values()])

        except ValueError as e:
            logger.error(f"Error deleting team: {str(e)}")
            emitter.emit_team_error(str(e))
        except Exception as e:
            logger.error(f"Unexpected error deleting team: {str(e)}")
            emitter.emit_team_error('Failed to delete team')

    @socketio.on('get_teams')
    def handle_get_teams():
        """Get all teams."""
        try:
            teams = team_manager.get_all_teams()
            emitter.emit_teams_list([team.to_dict() for team in teams.values()])
        except Exception as e:
            logger.error(f"Error getting teams: {str(e)}")
            emitter.emit_team_error('Failed to retrieve teams')

    @socketio.on('get_team')
    def handle_get_team(data):
        """Get a specific team."""
        try:
            team_id = data.get('team_id')
            if not team_id:
                emitter.emit_team_error('Team ID is required')
                return

            team = team_manager.get_team(team_id)
            if team:
                emitter.emit_team_data(team.to_dict())
            else:
                emitter.emit_team_error('Team not found')
        except Exception as e:
            logger.error(f"Error getting team: {str(e)}")
            emitter.emit_team_error('Failed to retrieve team')

    @socketio.on('turn_on_led')
    def handle_turn_on_led(data):
        """Turn on a team's LED."""
        try:
            team_id = data.get('team_id')
            if not team_id:
                emitter.emit_team_error('Team ID is required')
                return

            team = team_manager.get_team(team_id)
            if not team:
                emitter.emit_team_error('Team not found')
                return

            team.turn_on_led()
            logger.info(f"LED turned on for team: {team_id}")
            
            # Broadcast LED state change
            emitter.broadcast_led_state_changed(team_id, True)

        except Exception as e:
            logger.error(f"Error turning on LED for team {team_id}: {str(e)}")
            emitter.emit_team_error('Failed to turn on LED')

    @socketio.on('turn_off_led')
    def handle_turn_off_led(data):
        """Turn off a team's LED."""
        try:
            team_id = data.get('team_id')
            if not team_id:
                emitter.emit_team_error('Team ID is required')
                return

            team = team_manager.get_team(team_id)
            if not team:
                emitter.emit_team_error('Team not found')
                return

            team.turn_off_led()
            logger.info(f"LED turned off for team: {team_id}")
            
            # Broadcast LED state change
            emitter.broadcast_led_state_changed(team_id, False)

        except Exception as e:
            logger.error(f"Error turning off LED for team {team_id}: {str(e)}")
            emitter.emit_team_error('Failed to turn off LED')

    @socketio.on('toggle_led')
    def handle_toggle_led(data):
        """Toggle a team's LED."""
        try:
            team_id = data.get('team_id')
            if not team_id:
                emitter.emit_team_error('Team ID is required')
                return

            team = team_manager.get_team(team_id)
            if not team:
                emitter.emit_team_error('Team not found')
                return

            team.toggle_led()
            new_state = team.led_pin.gpio_pin.is_active if hasattr(team, 'led_pin') and hasattr(team.led_pin, 'gpio_pin') else False
            logger.info(f"LED toggled for team: {team_id}, new state: {new_state}")
            
            # Broadcast LED state change
            emitter.broadcast_led_state_changed(team_id, new_state)

        except Exception as e:
            logger.error(f"Error toggling LED for team {team_id}: {str(e)}")
            emitter.emit_team_error('Failed to toggle LED')

    @socketio.on('flash_led')
    def handle_flash_led(data):
        """Flash a team's LED."""
        try:
            team_id = data.get('team_id')
            flash_duration = data.get('flash_duration', 2.0)  # Default 2 seconds
            pulse_length = data.get('pulse_length', 0.2)  # Default 0.2 seconds
            
            if not team_id:
                emitter.emit_team_error('Team ID is required')
                return

            team = team_manager.get_team(team_id)
            if not team:
                emitter.emit_team_error('Team not found')
                return

            team.flash_led(flash_duration, pulse_length)
            logger.info(f"LED flashing for team: {team_id}, duration: {flash_duration}s")
            
            # Notify that LED is flashing
            emitter.broadcast_led_flashing(team_id, flash_duration)

        except Exception as e:
            logger.error(f"Error flashing LED for team {team_id}: {str(e)}")
            emitter.emit_team_error('Failed to flash LED')

    @socketio.on('reset_latch')
    def handle_reset_latch(data):
        """Reset a team's latch."""
        try:
            team_id = data.get('team_id')
            if not team_id:
                emitter.emit_team_error('Team ID is required')
                return

            team = team_manager.get_team(team_id)
            if not team:
                emitter.emit_team_error('Team not found')
                return

            team.reset_latch()
            logger.info(f"Latch reset for team: {team_id}")
            
            # Broadcast latch reset
            emitter.broadcast_latch_reset(team_id)

        except Exception as e:
            logger.error(f"Error resetting latch for team {team_id}: {str(e)}")
            emitter.emit_team_error('Failed to reset latch')

    @socketio.on('get_team_status')
    def handle_get_team_status(data):
        """Get current status of a team's hardware."""
        try:
            team_id = data.get('team_id')
            if not team_id:
                emitter.emit_team_error('Team ID is required')
                return

            team = team_manager.get_team(team_id)
            if not team:
                emitter.emit_team_error('Team not found')
                return

            status = {
                'team_id': team_id,
                'latch_state': team.latch_pin.gpio_pin.is_active if hasattr(team, 'latch_pin') and hasattr(team.latch_pin, 'gpio_pin') else False,
                'led_state': team.led_pin.gpio_pin.is_active if hasattr(team, 'led_pin') and hasattr(team.led_pin, 'gpio_pin') else False
            }
            
            emitter.emit_team_status(status)

        except Exception as e:
            logger.error(f"Error getting team status for {team_id}: {str(e)}")
            emitter.emit_team_error('Failed to get team status')
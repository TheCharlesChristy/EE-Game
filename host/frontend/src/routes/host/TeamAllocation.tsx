import { useAppState } from '../../state/store';

export function TeamAllocation() {
  const { teams, players, round, games, actions } = useAppState();
  const game = games.find((item) => item.id === round?.game_id);
  return (
    <section className="page-band">
      <div className="section-title">
        <h2>Team Allocation</h2>
        <p>{game?.team_capable ? `${game.team_size}-player target teams` : 'Current game is individual.'}</p>
      </div>
      <div className="toolbar">
        <button type="button" className="secondary" onClick={() => actions.previewTeams(game?.id)}>Preview</button>
        <button type="button" onClick={actions.confirmTeams} disabled={!game?.team_capable}>Confirm</button>
      </div>
      <div className="team-grid">
        {teams.map((team) => (
          <article key={team.team_id}>
            <h3>{team.team_name}</h3>
            <ul>
              {team.player_ids.map((playerId) => {
                const player = players.find((item) => item.player_id === playerId);
                return <li key={playerId}>{player?.username ?? playerId}</li>;
              })}
            </ul>
          </article>
        ))}
      </div>
    </section>
  );
}

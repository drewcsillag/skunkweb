/*
 * Database for hoptime project.
 * Time-stamp: <02/11/12 09:02:04 smulloni> 
 * $Id: hoptime.sql 1795 2007-08-27 21:04:08Z smulloni $
 */
DROP AGGREGATE cat TEXT;
DROP TABLE moves;
DROP SEQUENCE moves_id_seq;
DROP TABLE players;
DROP TABLE stories;
DROP SEQUENCE stories_id_seq;
DROP TABLE games;
DROP SEQUENCE games_id_seq;
DROP TABLE users;
DROP SEQUENCE users_id_seq;

CREATE TABLE users (
id SERIAL PRIMARY KEY,
username TEXT NOT NULL UNIQUE CHECK (username != 'guest'),
email TEXT NOT NULL,
honorific TEXT,
firstname TEXT,
middlename TEXT,
lastname TEXT,
password TEXT NOT NULL
);

CREATE TABLE games (
id SERIAL PRIMARY KEY,
title TEXT UNIQUE NOT NULL,
description TEXT,
owner INTEGER NOT NULL REFERENCES users,
quorum INTEGER DEFAULT 2,
capacity INTEGER DEFAULT 6,
created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
status VARCHAR(20) DEFAULT 'joining' 
  CHECK (status in ('joining', 'playing', 'editing', 'published', 'trashed')),
CONSTRAINT quorum_capacity_sanity_check CHECK (capacity > quorum)
);

CREATE TABLE players (
player INTEGER NOT NULL REFERENCES users,
game INTEGER NOT NULL REFERENCES games,
joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
play_number INTEGER,
PRIMARY KEY(player, game)
);

CREATE OR REPLACE FUNCTION next_play_number(INTEGER)
RETURNS INTEGER
AS '
DECLARE
   curgame ALIAS FOR $1;
   x INTEGER;
   cap INTEGER;
BEGIN
   SELECT INTO cap capacity 
   FROM games WHERE id=curgame;
   IF NOT FOUND THEN
       /* game is being created now */
       RETURN 0;
   END IF; 
   SELECT INTO x (1+MAX(play_number)) FROM players WHERE game=curgame;
   IF x IS NULL THEN
       RETURN 0;
   ELSE 
       IF x < cap THEN
           RETURN x;
       ELSE
           RETURN NULL;
       END IF;
   END IF;
END;' LANGUAGE 'plpgsql';

CREATE OR REPLACE FUNCTION set_play_number()
RETURNS opaque
AS '
DECLARE
  x INTEGER;
BEGIN
  x:=next_play_number(new.game);
  IF x=NULL THEN
     RAISE EXCEPTION ''Game Full'';
  ELSE
     new.play_number = x;
  END IF;
  RETURN new;
END;
' LANGUAGE 'plpgsql';
   
/* play order is determined at 
 *  the moment a player joins a game
 */
CREATE TRIGGER play_number_trigger BEFORE INSERT
ON players
FOR EACH ROW
EXECUTE PROCEDURE set_play_number();

/* a game owner (creator) is also 
 * its first (zero-th) player.
 * I'm using a trigger rather than a rule
 * so as to get at the game id, which
 * being a serial column is not available
 * until after the insert if has not been
 * specifically specified.
 */

CREATE OR REPLACE FUNCTION add_owner_as_player()
RETURNS opaque
AS '
BEGIN
  INSERT INTO players (player, game) VALUES (new.owner, new.id);
  RETURN new;
END;' LANGUAGE 'plpgsql';

CREATE TRIGGER add_owner_as_player_trigger AFTER INSERT
ON games 
FOR EACH ROW EXECUTE PROCEDURE add_owner_as_player();

CREATE TABLE moves (
id SERIAL PRIMARY KEY,
game INTEGER NOT NULL,
player INTEGER NOT NULL,
entered TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
content_append TEXT NOT NULL,
FOREIGN KEY(player, game) REFERENCES players);

/* 
 * when a game is ended and enters into the edit 
 * or published state, the text goes here 
 */
CREATE TABLE stories (
id SERIAL PRIMARY KEY,
game INTEGER NOT NULL UNIQUE REFERENCES games,
story text NOT NULL,
published TIMESTAMP);


/* concatenates text columns */
CREATE AGGREGATE cat(
  sfunc=textcat,
  basetype=text,
  stype=text,
  initcond='');

CREATE OR REPLACE FUNCTION get_text(INTEGER)
RETURNS TEXT
AS '
DECLARE
  story text;
BEGIN
  SELECT INTO story cat(content_append) 
  FROM (SELECT content_append FROM MOVES WHERE game=$1 ORDER BY entered) 
  AS content_append;
  RETURN story;
END;
' LANGUAGE 'plpgsql';
  
CREATE OR REPLACE FUNCTION game_update()
RETURNS opaque
AS '
DECLARE
  x integer;
BEGIN
  IF new.status=''editing'' OR new.status=''published'' THEN
     SELECT INTO x game FROM stories WHERE game=new.id;
     IF NOT FOUND THEN
         INSERT INTO stories (game, story) VALUES (new.id, get_text(new.id));
     END IF;
     IF new.status=''published'' THEN
         UPDATE stories SET published=CURRENT_TIMESTAMP WHERE game=new.id;
     END IF;
  END IF;
  RETURN new;
END;
' LANGUAGE 'plpgsql';

CREATE TRIGGER game_update_trigger AFTER UPDATE ON games
FOR EACH ROW EXECUTE PROCEDURE game_update();

CREATE OR REPLACE FUNCTION get_next_turn(INTEGER)
RETURNS INTEGER AS '
DECLARE
  game_id ALIAS FOR $1;
  game_status TEXT;
  game_size INTEGER;
  user_id INTEGER; 
  play_num INTEGER;
BEGIN
  SELECT into game_status status FROM games WHERE id=game_id;
  IF NOT FOUND OR game_status <> ''playing'' THEN
     RETURN NULL;
  END IF; 

  SELECT INTO game_size COUNT(*) FROM players where game=game_id;

  SELECT INTO play_num (1+p.play_number) % game_size FROM players p, moves m
    WHERE m.player=p.player
    AND m.game=game_id
    ORDER BY m.entered DESC LIMIT 1;
  IF NOT FOUND THEN
    play_num=0;
  END IF;
  SELECT INTO user_id player FROM players 
    WHERE game=game_id
    AND play_number=play_num;
  RETURN user_id;
END;
' LANGUAGE 'plpgsql';

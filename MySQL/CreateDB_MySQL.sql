DROP TABLE IF EXISTS `Monke`;
CREATE TABLE `Monke` (
    `timestamp` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `player_count` INTEGER NOT NULL,
    `room_name` TEXT,
    `game_version` TEXT,
    `game_name` TEXT,

    INDEX(`timestamp`),
    INDEX(`player_count`)
);

DROP TABLE IF EXISTS `Cache`;
CREATE TABLE `Cache` (
    `timestamp` DATETIME NOT NULL,
    `player_count` INTEGER NOT NULL,

    INDEX(`timestamp`),
    INDEX(`player_count`)
);
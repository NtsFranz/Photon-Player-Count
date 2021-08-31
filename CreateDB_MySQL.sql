DROP TABLE IF EXISTS `Monke`;
CREATE TABLE `Monke` (
    `timestamp` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `player_count` INTEGER NOT NULL,
    `room_name` TEXT NOT NULL,
    `game_version` TEXT NOT NULL,
    `game_name` TEXT NOT NULL,

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
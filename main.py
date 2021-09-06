import numpy
import requests
from tqdm import tqdm
from qrcode import QRCode, constants
import cv2
from blaseball_mike import models

game_id = '73523330-bff4-463f-a2b8-2ebe60dc06e5'

err_corr_level = {
    619: constants.ERROR_CORRECT_L,
    483: constants.ERROR_CORRECT_M,
    352: constants.ERROR_CORRECT_Q,
    259: constants.ERROR_CORRECT_H,
}


def err_corr_for_size(data_size: int):
    for qr_size in sorted(err_corr_level.keys()):
        if qr_size >= data_size:
            return err_corr_level[qr_size]

    raise RuntimeError(
        f"Can't make QR code with this version for {data_size} characters")


def main():
    game = requests.get("https://www.blaseball.com/database/feed/game", {
        'id': game_id,
        'sort': 1
    }).json()

    away = models.Team.load_at_time(game[0]['teamTags'][0], game[0]['created'])
    home = models.Team.load_at_time(game[0]['teamTags'][1], game[0]['created'])

    print(away.nickname, "away,", home.nickname, "home")

    # Reverse of the first half, because the beginning of the half will reverse
    # it again
    batting, fielding = home, away

    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    out = cv2.VideoWriter(game_id + ".avi", fourcc, 30.0, (154, 154))

    for event in tqdm(game, unit="frames"):
        if event['type'] == 2:
            batting, fielding = fielding, batting

        qr = QRCode(
            # Enough space for every event, and more importantly, 69x69px
            version=13,
            # Try to fill as much of the remaining space as possible with error
            # correction so the result has maximum visual noise
            error_correction=err_corr_for_size(len(event['description'])),
            # Teemsy
            box_size=2,
        )
        qr.add_data(event['description'])
        img_pil = qr.make_image(back_color=fielding.main_color,
                                fill_color=batting.main_color)

        img_cv = cv2.cvtColor(numpy.array(img_pil), cv2.COLOR_RGB2BGR)
        # cv2.imshow('qr', img_cv)
        # cv2.waitKey(1)
        out.write(img_cv)

    out.release()


if __name__ == '__main__':
    main()

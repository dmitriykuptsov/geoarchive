from dataclasses import dataclass

import numpy as np


@dataclass
class AffineTransformation:
    longitude_coefficients: tuple[float, float, float]
    latitude_coefficients: tuple[float, float, float]

    def pixel_to_wgs84(
        self,
        pixel_x: float,
        pixel_y: float,
    ) -> tuple[float, float]:
        a, b, c = (
            self.longitude_coefficients
        )

        d, e, f = (
            self.latitude_coefficients
        )

        longitude = (
            a * pixel_x
            + b * pixel_y
            + c
        )

        latitude = (
            d * pixel_x
            + e * pixel_y
            + f
        )

        return longitude, latitude


def calculate_affine_transformation(
    calibration_points,
) -> AffineTransformation:
    if len(calibration_points) < 3:
        raise ValueError(
            "At least 3 calibration points are required"
        )

    pixel_matrix = np.array(
        [
            [
                float(point.pixel_x),
                float(point.pixel_y),
                1.0,
            ]
            for point in calibration_points
        ],
        dtype=float,
    )

    longitude_values = np.array(
        [
            float(point.longitude)
            for point in calibration_points
        ],
        dtype=float,
    )

    latitude_values = np.array(
        [
            float(point.latitude)
            for point in calibration_points
        ],
        dtype=float,
    )

    longitude_coefficients = (
        np.linalg.lstsq(
            pixel_matrix,
            longitude_values,
            rcond=None,
        )[0]
    )

    latitude_coefficients = (
        np.linalg.lstsq(
            pixel_matrix,
            latitude_values,
            rcond=None,
        )[0]
    )

    return AffineTransformation(
        longitude_coefficients=tuple(
            longitude_coefficients
        ),
        latitude_coefficients=tuple(
            latitude_coefficients
        ),
    )

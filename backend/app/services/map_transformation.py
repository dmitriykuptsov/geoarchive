from dataclasses import dataclass

import numpy as np
import math

@dataclass
class CalibrationError:
    rmse_meters: float
    max_error_meters: float

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

    def calculate_error(
        self,
        calibration_points,
    ) -> CalibrationError:

        errors = []

        for point in calibration_points:
            predicted_longitude, predicted_latitude = (
                self.pixel_to_wgs84(
                    float(point.pixel_x),
                    float(point.pixel_y),
                )
            )

            longitude_error = (
                predicted_longitude
                - float(point.longitude)
            )

            latitude_error = (
                predicted_latitude
                - float(point.latitude)
            )

            latitude_radians = math.radians(
                float(point.latitude)
            )

            east_west_error = (
                longitude_error
                * 111_320
                * math.cos(latitude_radians)
            )

            north_south_error = (
                latitude_error
                * 111_320
            )

            error_meters = math.sqrt(
                east_west_error ** 2
                + north_south_error ** 2
            )

            errors.append(
                error_meters
            )

        rmse_meters = math.sqrt(
            sum(
                error ** 2
                for error in errors
            )
            / len(errors)
        )

        max_error_meters = max(
            errors
        )

        return CalibrationError(
            rmse_meters=rmse_meters,
            max_error_meters=max_error_meters,
        )


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

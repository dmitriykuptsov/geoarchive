from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    Form,
)
from fastapi.responses import FileResponse

from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy import delete

from sqlalchemy.exc import IntegrityError

from pathlib import Path
from uuid import uuid4
from PIL import Image

from app.models.deposit import (
    Deposit,
)

from app.models.map import (
    Map,
    MapFile,
    MapCalibrationPoint,
)

from app.models.borehole import (
    Borehole
)

from app.models.contour import (
    Contour,
    ContourPoint
)

from app.models.user import (
    User,
)

from app.schemas.map import (
    MapCreate,
    MapResponse,
    MapUpdate,
    MapFileResponse,
    MapCalibrationPointCreate,
    MapCalibrationPointResponse,
    MapCalibrationPointUpdate,
    AffineTransformationResponse,
    CalibrationErrorResponse,
    WGS84CoordinateResponse,
    PixelCoordinateRequest
)

from app.schemas.borehole import (
    BoreholeCreate,
    BoreholeUpdate,
    BoreholeResponse
)

from app.schemas.contour import (
    ContourCreate,
    ContourPointCreate,
    ContourPointResponse,
    ContourResponse,
    ContourUpdate
)

from app.core.dependencies import (
    get_db,
    require_password_changed,
)

from app.services.deposit_access import (
    can_view_deposit,
    can_edit_deposit,
    can_administer_deposit,
    is_global_admin,
)

from app.services.storage import FileStorage, file_storage
from app.services.map_transformation import calculate_affine_transformation

router = APIRouter()


@router.post(
    "/deposits/{deposit_id}",
    response_model=MapResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_map(
    deposit_id: int,
    data: MapCreate,
    db: Session = Depends(
        get_db,
    ),
    current_user: User = Depends(
        require_password_changed,
    ),
):
    deposit = db.get(
        Deposit,
        deposit_id,
    )

    if deposit is None:

        raise HTTPException(
            status_code=404,
            detail="Deposit not found",
        )

    if not can_edit_deposit(
        db,
        current_user,
        deposit,
    ) and not is_global_admin(db=db, user=current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=("Edit access required"),
        )

    geological_map = Map(
        deposit_id=deposit_id,
        name=data.name,
        description=data.description,
        map_type=data.map_type,
        coordinate_system=(data.coordinate_system),
        created_by=current_user.id,
    )

    try:
        db.add(
            geological_map,
        )

        db.commit()

    except IntegrityError as exc:

        db.rollback()

        if "uq_map_deposit_name" in str(exc.orig):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=("A map with this name " "already exists in this deposit."),
            )

        raise

    return geological_map


@router.get(
    "/deposits/{deposit_id}",
    response_model=list[MapResponse],
)
def get_maps(
    deposit_id: int,
    db: Session = Depends(
        get_db,
    ),
    current_user: User = Depends(
        require_password_changed,
    ),
):
    deposit = db.get(
        Deposit,
        deposit_id,
    )

    if deposit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deposit not found",
        )

    if not (
        is_global_admin(
            db=db,
            user=current_user,
        )
        or can_view_deposit(
            db,
            current_user,
            deposit,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="View access required",
        )

    maps = db.scalars(
        select(Map)
        .where(
            Map.deposit_id == deposit_id,
        )
        .order_by(
            Map.id,
        )
    ).all()

    return maps


@router.get(
    "/{map_id}",
    response_model=MapResponse,
)
def get_map(
    map_id: int,
    db: Session = Depends(
        get_db,
    ),
    current_user: User = Depends(
        require_password_changed,
    ),
):
    geological_map = db.get(
        Map,
        map_id,
    )

    if geological_map is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map not found",
        )

    deposit = db.get(
        Deposit,
        geological_map.deposit_id,
    )

    if not is_global_admin(
        db=db,
        user=current_user,
    ) and not can_view_deposit(
        db,
        current_user,
        deposit,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="View access required",
        )

    return geological_map


@router.patch(
    "/{map_id}",
    response_model=MapResponse,
)
def update_map(
    map_id: int,
    data: MapUpdate,
    db: Session = Depends(
        get_db,
    ),
    current_user: User = Depends(
        require_password_changed,
    ),
):
    geological_map = db.get(
        Map,
        map_id,
    )

    if geological_map is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map not found",
        )

    deposit = db.get(
        Deposit,
        geological_map.deposit_id,
    )

    if not is_global_admin(
        db=db,
        user=current_user,
    ) and not can_edit_deposit(
        db,
        current_user,
        deposit,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Edit access required",
        )

    update_data = data.model_dump(
        exclude_unset=True,
    )

    for field, value in update_data.items():

        setattr(
            geological_map,
            field,
            value,
        )

    try:

        db.commit()

    except IntegrityError as exc:

        db.rollback()

        if "uq_map_deposit_name" in str(exc.orig):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=("A map with this name " "already exists in this deposit."),
            )

        raise

    db.refresh(
        geological_map,
    )

    return geological_map


@router.delete(
    "/{map_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_map(
    map_id: int,
    db: Session = Depends(
        get_db,
    ),
    current_user: User = Depends(
        require_password_changed,
    ),
):
    geological_map = db.get(
        Map,
        map_id,
    )

    if geological_map is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map not found",
        )

    deposit = db.get(
        Deposit,
        geological_map.deposit_id,
    )

    if not is_global_admin(
        db=db,
        user=current_user,
    ) and not can_edit_deposit(
        db,
        current_user,
        deposit,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Edit access required",
        )

    db.delete(
        geological_map,
    )

    db.commit()

    return None


@router.post(
    "/{map_id}/files",
    response_model=MapFileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_map_file(
    map_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(
        get_db,
    ),
    current_user: User = Depends(
        require_password_changed,
    ),
):

    geological_map = db.get(
        Map,
        map_id,
    )

    if geological_map is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map not found",
        )

    deposit = db.get(
        Deposit,
        geological_map.deposit_id,
    )

    if not is_global_admin(
        db=db,
        user=current_user,
    ) and not can_edit_deposit(
        db,
        current_user,
        deposit,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Edit access required",
        )

    allowed_types = {
        "image/jpeg",
        "image/png",
        "image/tiff",
    }

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported map file type",
        )

    storage_filename = f"{uuid4()}" f"{Path(file.filename).suffix.lower()}"

    (
        storage_path,
        file_size,
        checksum,
    ) = await file_storage.save(
        file=file,
        category="maps",
        deposit_id=deposit.id,
        storage_filename=storage_filename,
    )

    destination = file_storage.base_path / storage_path

    with Image.open(destination) as image:
        width, height = image.size

    map_file = MapFile(
        map_id=geological_map.id,
        file_type="ORIGINAL",
        storage_path=storage_path,
        mime_type=file.content_type,
        file_size=file_size,
        width=width,
        height=height,
    )

    try:
        db.add(
            map_file,
        )

        db.commit()

    except Exception:
        db.rollback()

        file_storage.delete(
            storage_path,
        )

        raise

    db.refresh(
        map_file,
    )

    return map_file


@router.delete(
    "/{map_id}/files/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_map_file(
    map_id: int,
    file_id: int,
    db: Session = Depends(
        get_db,
    ),
    current_user: User = Depends(
        require_password_changed,
    ),
):
    map_file = db.scalar(
        select(MapFile).where(
            MapFile.id == file_id,
            MapFile.map_id == map_id,
        )
    )

    if map_file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map file not found",
        )

    geological_map = db.get(
        Map,
        map_id,
    )

    if geological_map is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map not found",
        )

    deposit = db.get(
        Deposit,
        geological_map.deposit_id,
    )

    if not is_global_admin(
        db=db,
        user=current_user,
    ) and not can_edit_deposit(
        db,
        current_user,
        deposit,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Edit access required",
        )

    file_storage.delete(
        map_file.storage_path,
    )

    db.delete(
        map_file,
    )

    db.commit()

    return None


@router.get(
    "/{map_id}/files/{file_id}",
)
def get_map_file(
    map_id: int,
    file_id: int,
    db: Session = Depends(
        get_db,
    ),
    current_user: User = Depends(
        require_password_changed,
    ),
):
    map_file = db.scalar(
        select(MapFile).where(
            MapFile.id == file_id,
            MapFile.map_id == map_id,
        )
    )

    if map_file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map file not found",
        )

    geological_map = db.get(
        Map,
        map_id,
    )

    if geological_map is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map not found",
        )

    deposit = db.get(
        Deposit,
        geological_map.deposit_id,
    )

    if not is_global_admin(
        db=db,
        user=current_user,
    ) and not can_view_deposit(
        db,
        current_user,
        deposit,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="View access required",
        )

    file_path = file_storage.base_path / map_file.storage_path

    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Physical file not found",
        )

    return FileResponse(
        path=file_path,
        media_type=map_file.mime_type,
        filename=(f"map-{map_file.id}" f"{Path(map_file.storage_path).suffix}"),
    )


@router.get(
    "/{map_id}/files",
    response_model=list[MapFileResponse],
)
def list_map_files(
    map_id: int,
    db: Session = Depends(
        get_db,
    ),
    current_user: User = Depends(
        require_password_changed,
    ),
):
    geological_map = db.get(
        Map,
        map_id,
    )

    if geological_map is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map not found",
        )

    deposit = db.get(
        Deposit,
        geological_map.deposit_id,
    )

    if not is_global_admin(
        db=db,
        user=current_user,
    ) and not can_view_deposit(
        db,
        current_user,
        deposit,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="View access required",
        )

    map_files = db.scalars(
        select(MapFile)
        .where(
            MapFile.map_id == map_id,
        )
        .order_by(
            MapFile.id,
        )
    ).all()

    return map_files


@router.post(
    "/{map_id}/calibration-points",
    response_model=MapCalibrationPointResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_calibration_point(
    map_id: int,
    payload: MapCalibrationPointCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_password_changed,
    ),
):
    geological_map = db.get(
        Map,
        map_id,
    )

    if geological_map is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map not found",
        )

    deposit = db.get(
        Deposit,
        geological_map.deposit_id,
    )

    if not is_global_admin(
        db=db,
        user=current_user,
    ) and not can_edit_deposit(
        db,
        current_user,
        deposit,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Edit access required",
        )

    calibration_point = MapCalibrationPoint(
        map_id=map_id,
        pixel_x=payload.pixel_x,
        pixel_y=payload.pixel_y,
        longitude=payload.longitude,
        latitude=payload.latitude,
    )

    db.add(
        calibration_point,
    )

    db.commit()

    db.refresh(
        calibration_point,
    )

    return calibration_point


@router.get(
    "/{map_id}/calibration-points",
    response_model=list[MapCalibrationPointResponse],
)
def list_calibration_points(
    map_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_password_changed,
    ),
):
    geological_map = db.get(
        Map,
        map_id,
    )

    if geological_map is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map not found",
        )

    deposit = db.get(
        Deposit,
        geological_map.deposit_id,
    )

    if not is_global_admin(
        db=db,
        user=current_user,
    ) and not can_view_deposit(
        db,
        current_user,
        deposit,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="View access required",
        )

    calibration_points = db.scalars(
        select(MapCalibrationPoint)
        .where(
            MapCalibrationPoint.map_id == map_id,
        )
        .order_by(
            MapCalibrationPoint.id,
        )
    ).all()

    return calibration_points


@router.patch(
    "/{map_id}/calibration-points/{point_id}",
    response_model=MapCalibrationPointResponse,
)
def update_calibration_point(
    map_id: int,
    point_id: int,
    payload: MapCalibrationPointUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_password_changed,
    ),
):
    calibration_point = db.scalar(
        select(MapCalibrationPoint).where(
            MapCalibrationPoint.id == point_id,
            MapCalibrationPoint.map_id == map_id,
        )
    )

    if calibration_point is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calibration point not found",
        )

    geological_map = db.get(
        Map,
        map_id,
    )

    if geological_map is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map not found",
        )

    deposit = db.get(
        Deposit,
        geological_map.deposit_id,
    )

    if not is_global_admin(
        db=db,
        user=current_user,
    ) and not can_edit_deposit(
        db,
        current_user,
        deposit,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Edit access required",
        )

    update_data = payload.model_dump(
        exclude_unset=True,
    )

    for field, value in update_data.items():
        setattr(
            calibration_point,
            field,
            value,
        )

    db.commit()

    db.refresh(
        calibration_point,
    )

    return calibration_point


@router.delete(
    "/{map_id}/calibration-points/{point_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_calibration_point(
    map_id: int,
    point_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_password_changed,
    ),
):
    calibration_point = db.scalar(
        select(MapCalibrationPoint).where(
            MapCalibrationPoint.id == point_id,
            MapCalibrationPoint.map_id == map_id,
        )
    )

    if calibration_point is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calibration point not found",
        )

    geological_map = db.get(
        Map,
        map_id,
    )

    if geological_map is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map not found",
        )

    deposit = db.get(
        Deposit,
        geological_map.deposit_id,
    )

    if not is_global_admin(
        db=db,
        user=current_user,
    ) and not can_edit_deposit(
        db,
        current_user,
        deposit,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Edit access required",
        )

    db.delete(
        calibration_point,
    )

    db.commit()

    return None

@router.post(
    "/{map_id}/calibration/solve",
    response_model=AffineTransformationResponse,
)
def solve_map_calibration(
    map_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_password_changed,
    ),
):
    geological_map = db.get(
        Map,
        map_id,
    )

    if geological_map is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map not found",
        )

    deposit = db.get(
        Deposit,
        geological_map.deposit_id,
    )

    if (
        not is_global_admin(
            db=db,
            user=current_user,
        )
        and not can_view_deposit(
            db,
            current_user,
            deposit,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="View access required",
        )

    calibration_points = db.scalars(
        select(MapCalibrationPoint)
        .where(
            MapCalibrationPoint.map_id == map_id,
        )
        .order_by(
            MapCalibrationPoint.id,
        )
    ).all()

    if len(calibration_points) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "At least 3 calibration points "
                "are required"
            ),
        )

    transformation = (
        calculate_affine_transformation(
            calibration_points,
        )
    )

    error = (
        transformation.calculate_error(
            calibration_points,
        )
    )

    return AffineTransformationResponse(
        longitude_coefficients=(
            transformation.longitude_coefficients
        ),
        latitude_coefficients=(
            transformation.latitude_coefficients
        ),
        error=CalibrationErrorResponse(
            rmse_meters=(
                error.rmse_meters
            ),
            max_error_meters=(
                error.max_error_meters
            ),
        ),
    )

@router.post(
    "/{map_id}/calibration/transform",
    response_model=WGS84CoordinateResponse,
)
def transform_pixel_coordinate(
    map_id: int,
    payload: PixelCoordinateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_password_changed,
    ),
):
    geological_map = db.get(
        Map,
        map_id,
    )

    if geological_map is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map not found",
        )

    deposit = db.get(
        Deposit,
        geological_map.deposit_id,
    )

    if (
        not is_global_admin(
            db=db,
            user=current_user,
        )
        and not can_view_deposit(
            db,
            current_user,
            deposit,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="View access required",
        )

    calibration_points = db.scalars(
        select(MapCalibrationPoint)
        .where(
            MapCalibrationPoint.map_id == map_id,
        )
        .order_by(
            MapCalibrationPoint.id,
        )
    ).all()

    if len(calibration_points) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "At least 3 calibration points "
                "are required"
            ),
        )

    transformation = (
        calculate_affine_transformation(
            calibration_points,
        )
    )

    longitude, latitude = (
        transformation.pixel_to_wgs84(
            float(payload.pixel_x),
            float(payload.pixel_y),
        )
    )

    return WGS84CoordinateResponse(
        pixel_x=payload.pixel_x,
        pixel_y=payload.pixel_y,
        longitude=longitude,
        latitude=latitude,
    )

@router.post(
    "/{map_id}/boreholes",
    response_model=BoreholeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_borehole(
    map_id: int,
    payload: BoreholeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_password_changed,
    ),
):

    geological_map = db.get(
        Map,
        map_id,
    )

    if geological_map is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map not found",
        )

    deposit = db.get(
        Deposit,
        geological_map.deposit_id,
    )

    if (
        not is_global_admin(
            db=db,
            user=current_user,
        )
        and not can_edit_deposit(
            db,
            current_user,
            deposit,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Edit access required",
        )

    calibration_points = db.scalars(
        select(MapCalibrationPoint)
        .where(
            MapCalibrationPoint.map_id == map_id,
        )
        .order_by(
            MapCalibrationPoint.id,
        )
    ).all()

    if len(calibration_points) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "At least 3 calibration points "
                "are required"
            ),
        )

    transformation = (
        calculate_affine_transformation(
            calibration_points,
        )
    )

    longitude, latitude = (
        transformation.pixel_to_wgs84(
            float(payload.pixel_x),
            float(payload.pixel_y),
        )
    )

    borehole = Borehole(
        map_id=map_id,
        name=payload.name,
        description=payload.description,
        pixel_x=payload.pixel_x,
        pixel_y=payload.pixel_y,
        longitude=longitude,
        latitude=latitude,
    )

    try:
        db.add(
            borehole,
        )

        db.commit()

    except IntegrityError as exc:
        db.rollback()

        if (
            "uq_borehole_map_name"
            in str(exc.orig)
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "A borehole with this name "
                    "already exists on this map"
                ),
            )

        raise

    return borehole

@router.get(
    "/{map_id}/boreholes",
    response_model=list[BoreholeResponse],
)
def list_boreholes(
    map_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_password_changed,
    ),
):
    geological_map = db.get(
        Map,
        map_id,
    )

    if geological_map is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map not found",
        )

    deposit = db.get(
        Deposit,
        geological_map.deposit_id,
    )

    if (
        not is_global_admin(
            db=db,
            user=current_user,
        )
        and not can_view_deposit(
            db,
            current_user,
            deposit,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="View access required",
        )

    boreholes = db.scalars(
        select(Borehole)
        .where(
            Borehole.map_id == map_id,
        )
        .order_by(
            Borehole.id,
        )
    ).all()

    return boreholes

@router.get(
    "/{map_id}/boreholes/{borehole_id}",
    response_model=BoreholeResponse,
)
def get_borehole(
    map_id: int,
    borehole_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_password_changed,
    ),
):
    borehole = db.scalar(
        select(Borehole).where(
            Borehole.id == borehole_id,
            Borehole.map_id == map_id,
        )
    )

    if borehole is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Borehole not found",
        )

    geological_map = db.get(
        Map,
        map_id,
    )

    deposit = db.get(
        Deposit,
        geological_map.deposit_id,
    )

    if (
        not is_global_admin(
            db=db,
            user=current_user,
        )
        and not can_view_deposit(
            db,
            current_user,
            deposit,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="View access required",
        )

    return borehole

@router.patch(
    "/{map_id}/boreholes/{borehole_id}",
    response_model=BoreholeResponse,
)
def update_borehole(
    map_id: int,
    borehole_id: int,
    payload: BoreholeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_password_changed,
    ),
):

    borehole = db.scalar(
        select(Borehole).where(
            Borehole.id == borehole_id,
            Borehole.map_id == map_id,
        )
    )

    if borehole is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Borehole not found",
        )

    update_data = payload.model_dump(
        exclude_unset=True,
    )

    if "name" in update_data:
        borehole.name = (
            update_data["name"]
        )

    if "description" in update_data:
        borehole.description = (
            update_data["description"]
        )

    pixel_x = (
        update_data.get(
            "pixel_x",
            borehole.pixel_x,
        )
    )

    pixel_y = (
        update_data.get(
            "pixel_y",
            borehole.pixel_y,
        )
    )

    if (
        "pixel_x" in update_data
        or "pixel_y" in update_data
    ):
        calibration_points = db.scalars(
            select(
                MapCalibrationPoint,
            )
            .where(
                MapCalibrationPoint.map_id
                == map_id,
            )
        ).all()

        if len(calibration_points) < 3:
            raise HTTPException(
                status_code=(
                    status.HTTP_400_BAD_REQUEST
                ),
                detail=(
                    "At least 3 calibration "
                    "points are required"
                ),
            )

        transformation = (
            calculate_affine_transformation(
                calibration_points,
            )
        )

        longitude, latitude = (
            transformation.pixel_to_wgs84(
                float(pixel_x),
                float(pixel_y),
            )
        )

        borehole.pixel_x = pixel_x
        borehole.pixel_y = pixel_y
        borehole.longitude = longitude
        borehole.latitude = latitude

    try:

        db.commit()

    except IntegrityError as exc:
        db.rollback()

        if (
            "uq_borehole_map_name"
            in str(exc.orig)
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "A borehole with this name "
                    "already exists on this map"
                ),
            )

        raise

    return borehole

@router.delete(
    "/{map_id}/boreholes/{borehole_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_borehole(
    map_id: int,
    borehole_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_password_changed,
    ),
):
    borehole = db.scalar(
        select(Borehole).where(
            Borehole.id == borehole_id,
            Borehole.map_id == map_id,
        )
    )

    if borehole is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Borehole not found",
        )

    geological_map = db.get(
        Map,
        map_id,
    )

    deposit = db.get(
        Deposit,
        geological_map.deposit_id,
    )

    if (
        not is_global_admin(
            db=db,
            user=current_user,
        )
        and not can_edit_deposit(
            db,
            current_user,
            deposit,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Edit access required",
        )

    db.delete(
        borehole,
    )

    db.commit()

    return None

@router.post(
    "/{map_id}/contours",
    response_model=ContourResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_contour(
    map_id: int,
    payload: ContourCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_password_changed,
    ),
):

    geological_map = db.get(
        Map,
        map_id,
    )

    if geological_map is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map not found",
        )

    deposit = db.get(
        Deposit,
        geological_map.deposit_id,
    )

    if (
        not is_global_admin(
            db=db,
            user=current_user,
        )
        and not can_edit_deposit(
            db,
            current_user,
            deposit,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Edit access required",
        )

    calibration_points = db.scalars(
        select(MapCalibrationPoint)
        .where(
            MapCalibrationPoint.map_id == map_id,
        )
        .order_by(
            MapCalibrationPoint.id,
        )
    ).all()

    if len(calibration_points) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "At least 3 calibration points "
                "are required"
            ),
        )

    transformation = (
        calculate_affine_transformation(
            calibration_points,
        )
    )

    contour = Contour(
        map_id=map_id,
        name=payload.name,
        description=payload.description,
    )

    for sequence, point in enumerate(
        payload.points
    ):
        longitude, latitude = (
            transformation.pixel_to_wgs84(
                float(point.pixel_x),
                float(point.pixel_y),
            )
        )

        contour.points.append(
            ContourPoint(
                sequence=sequence,
                pixel_x=point.pixel_x,
                pixel_y=point.pixel_y,
                longitude=longitude,
                latitude=latitude,
            )
        )

    db.add(
        contour,
    )

    try:
        db.commit()

    except IntegrityError as exc:
        db.rollback()

        if (
            "uq_contour_map_name"
            in str(exc.orig)
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "A contour with this name "
                    "already exists on this map"
                ),
            )

        raise
    return contour


@router.get(
    "/{map_id}/contours",
    response_model=list[ContourResponse],
)
def list_contours(
    map_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_password_changed,
    ),
):

    geological_map = db.get(
        Map,
        map_id,
    )

    if geological_map is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map not found",
        )

    deposit = db.get(
        Deposit,
        geological_map.deposit_id,
    )

    if (
        not is_global_admin(
            db=db,
            user=current_user,
        )
        and not can_view_deposit(
            db,
            current_user,
            deposit,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="View access required",
        )
    
    contours = db.scalars(
        select(Contour)
        .where(
            Contour.map_id == map_id,
        )
        .order_by(
            Contour.id,
        )
    ).all()

    return contours

@router.get(
    "/{map_id}/contours/{contour_id}",
    response_model=ContourResponse,
)
def get_contour(
    map_id: int,
    contour_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_password_changed,
    ),
):

    geological_map = db.get(
        Map,
        map_id,
    )

    if geological_map is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map not found",
        )

    deposit = db.get(
        Deposit,
        geological_map.deposit_id,
    )

    if (
        not is_global_admin(
            db=db,
            user=current_user,
        )
        and not can_view_deposit(
            db,
            current_user,
            deposit,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="View access required",
        )

    contour = db.scalar(
        select(Contour)
        .where(
            Contour.id == contour_id,
            Contour.map_id == map_id,
        )
    )

    if contour is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contour not found",
        )

    return contour

@router.patch(
    "/{map_id}/contours/{contour_id}",
    response_model=ContourResponse,
)
def update_contour(
    map_id: int,
    contour_id: int,
    payload: ContourUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_password_changed,
    ),
):

    geological_map = db.get(
        Map,
        map_id,
    )

    if geological_map is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map not found",
        )

    deposit = db.get(
        Deposit,
        geological_map.deposit_id,
    )

    if (
        not is_global_admin(
            db=db,
            user=current_user,
        )
        and not can_view_deposit(
            db,
            current_user,
            deposit,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="View access required",
        )

    contour = db.scalar(
        select(Contour)
        .where(
            Contour.id == contour_id,
            Contour.map_id == map_id,
        )
    )

    if contour is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contour not found",
        )

    update_data = payload.model_dump(
        exclude_unset=True,
    )

    if "name" in update_data:
        contour.name = update_data[
            "name"
        ]

    if "description" in update_data:
        contour.description = update_data[
            "description"
        ]

    calibration_points = db.scalars(
        select(MapCalibrationPoint)
        .where(
            MapCalibrationPoint.map_id == map_id,
        )
        .order_by(
            MapCalibrationPoint.id,
        )
    ).all()

    if len(calibration_points) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "At least 3 calibration points "
                "are required"
            ),
        )

    transformation = (
        calculate_affine_transformation(
            calibration_points,
        )
    )

    contour.points.clear()

    if "points" in update_data:

        db.execute(
            delete(ContourPoint).where(
                ContourPoint.contour_id
                == contour.id
            )
        )

        # Flush the DELETE immediately
        db.flush()

        for sequence, point in enumerate(
            payload.points
        ):
            longitude, latitude = (
                transformation.pixel_to_wgs84(
                    float(point.pixel_x),
                    float(point.pixel_y),
                )
            )

            contour.points.append(
                ContourPoint(
                    sequence=sequence,
                    pixel_x=point.pixel_x,
                    pixel_y=point.pixel_y,
                    longitude=longitude,
                    latitude=latitude,
                )
            )

    try:
        db.commit()

    except IntegrityError as exc:
        db.rollback()

        if (
            "uq_contour_map_name"
            in str(exc.orig)
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "A contour with this name "
                    "already exists on this map"
                ),
            )

        raise

    db.refresh(
        contour,
    )

    return contour

@router.delete(
    "/{map_id}/contours/{contour_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_contour(
    map_id: int,
    contour_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_password_changed,
    ),
):
    
    geological_map = db.get(
        Map,
        map_id,
    )

    if geological_map is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map not found",
        )

    deposit = db.get(
            Deposit,
            geological_map.deposit_id,
        )

    if (
        not is_global_admin(
            db=db,
            user=current_user,
        )
        and not can_view_deposit(
            db,
            current_user,
            deposit,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="View access required",
        )

    contour = db.scalar(
        select(Contour)
        .where(
            Contour.id == contour_id,
            Contour.map_id == map_id,
        )
    )

    if contour is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contour not found",
        )

    db.delete(
        contour,
    )

    db.commit()

    return None
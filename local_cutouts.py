from astropy.io import fits
from astropy.wcs import WCS
import numpy as np
from astropy.coordinates import SkyCoord
import astropy.units as u
import matplotlib.pyplot as plt

def make_multiple_cutouts(image, sky_coords, size=61):
    """
    Extracts square cutouts from a FITS image at specified sky coordinates.

    Parameters:
    - image: Path to the FITS image file.
    - sky_coords: An astropy.coordinates.SkyCoord object with the sky positions.
    - size: The size of the square cutout (must be an odd integer, default is 61).

    Returns:
    - cutouts: List of 2D NumPy arrays representing the extracted cutouts.
    """
    # Load the image data and header from the FITS file
    array = fits.getdata(image)
    header = fits.getheader(image)

    # Remove any axes of size 1 (e.g., unused axes in radio images)
    array = np.squeeze(array)

    # Create a WCS (World Coordinate System) object from the header
    wcs = WCS(header)

    # Extract only the celestial part of the WCS
    wcs_celestial = wcs.celestial

    # Convert sky coordinates to pixel coordinates using the celestial WCS
    x_pix, y_pix = wcs_celestial.world_to_pixel(sky_coords)

    # Calculate half the size to determine the radius of the cutout
    half_size = size // 2
    # Initialize a list to store the cutouts
    cutouts = []

    # Iterate over each pixel coordinate pair
    for x, y in zip(x_pix, y_pix):
        # Ensure coordinates are integers
        x, y = int(round(x)), int(round(y))

        # Create a square array filled with NaNs to hold the cutout
        cutout = np.full((size, size), np.nan)

        # Determine the start and end indices for slicing the input array
        x_start = max(0, x - half_size)
        x_end = min(array.shape[1], x + half_size + 1)
        y_start = max(0, y - half_size)
        y_end = min(array.shape[0], y + half_size + 1)

        # Determine the corresponding start and end indices for the cutout array
        cutout_x_start = max(0, half_size - x)
        cutout_x_end = cutout_x_start + (x_end - x_start)
        cutout_y_start = max(0, half_size - y)
        cutout_y_end = cutout_y_start + (y_end - y_start)

        # Check if there is any overlap between the array slice and the cutout region
        if x_end > x_start and y_end > y_start:
            # Extract the relevant regions from both the cutout and the array
            cutout_region = cutout[cutout_y_start:cutout_y_end, cutout_x_start:cutout_x_end]
            array_region = array[y_start:y_end, x_start:x_end]

            # Determine the minimal shape to avoid indexing errors
            min_y = min(cutout_region.shape[0], array_region.shape[0])
            min_x = min(cutout_region.shape[1], array_region.shape[1])

            # Copy the array region into the cutout
            cutout_region[:min_y, :min_x] = array_region[:min_y, :min_x]

        # Add the cutout to the list
        cutouts.append(cutout)

    # Return all the cutouts
    return cutouts




# Example


# Define the image file path
image_file = './test_data/VLASS2.2.ql.T01t38.J183232-383000.10.2048.v1.I.iter1.image.pbcor.tt0.subim.fits'

# Define sky coordinates (one coordinate around a bright source, one on the edge of the image, and one off the image)
ra_list = ['18h32m02s', '18h29m54s', '18h39m54s']
dec_list = ['-38d30m31s', '-38d26m30s', '-38d26m30s']
descriptions = ['bright source', 'edge of image', 'not contained in image']

# Convert to SkyCoord objects
sky_coords = SkyCoord(ra=ra_list, dec=dec_list, frame='icrs')

# Call the modified function to get cutouts
cutouts = make_multiple_cutouts(image_file, sky_coords, size=61)

# Plot the cutouts using matplotlib
for i, cutout in enumerate(cutouts):
    plt.figure(figsize=(6, 6))
    plt.imshow(cutout, origin='lower', cmap='gray', interpolation='nearest')
    plt.colorbar(label='Intensity')
    plt.title(f'{descriptions[i]}\n RA={ra_list[i]}, Dec={dec_list[i]}')
    plt.xlabel('Pixel X')
    plt.ylabel('Pixel Y')
    plt.show()

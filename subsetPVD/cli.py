import click
import math
import tarfile
import os.path
import xml.etree.ElementTree as ET


def create_subset_pvd(infilename, outfilename,
                      nsubset=0, t_step=0.0, inc_final=True):
    """
    Generate a PVD file for a subset of provided file based on provided
    criterion. Assumes DataSet elements each refer to data for a single
    timestep, and the time information is included.
    """
    soln_file = ET.parse(infilename)
    elems = soln_file.findall('.//DataSet')
    n_full = len(elems)
    coll_elem = soln_file.find('.//Collection')
    subset = elems
    if(t_step > 0.0):
        tlast = float(elems[0].get('timestep'))
        tnext = float(elems[0].get('timestep'))
        tfinal = float(elems[-1].get('timestep'))
        subset = []
        for e in elems:
            tcurr = float(e.get('timestep'))
            if(tcurr >= tnext):
                subset.append(e)
                ndiff = math.floor((tcurr-tlast)/t_step)
                tnext = tlast + (ndiff+1.)*t_step
        if(inc_final and tlast < tfinal):
            subset.append(elems[-1])
    elif(nsubset > 2):
        if(n_full > nsubset):
            step = int(n_full / nsubset)
            subset = elems[0:-1:step]
            if inc_final:
                subset[-1] = elems[-1]
    else:
        raise ValueError("Could not generate subset file, no criterion given")
    coll_elem[:] = subset

    soln_file.write(outfilename)


def get_req_file_list_pvd(source_pvd):
    """
    Create list of files referenced by given PVD file
    """
    flist = []
    flist.append(source_pvd)

    src_dir = os.path.dirname(source_pvd)
    source_tree = ET.parse(source_pvd)
    elems = source_tree.findall('.//DataSet')
    for e in elems:
        subfile = e.get('file')
        sub_fullpath = os.path.join(src_dir, subfile)
        sub_full_dir = os.path.dirname(sub_fullpath)
        flist.append(sub_fullpath)
        sub_tree = ET.parse(sub_fullpath)
        subelems = sub_tree.findall('.//Piece')
        for e2 in subelems:
            leaf = e2.get('Source')
            leaf_path = os.path.join(sub_full_dir, leaf)
            flist.append(leaf_path)
    return flist


def archive_files(archive_fileprefix, flist, zip_type, reldir, prefix=""):
    """
    Combine files in list into tar archive
    """
    def archive_filter(tinfo):
        fdir, fbase = os.path.split(tinfo.name)
        archpath = os.path.join(prefix, os.path.relpath(tinfo.name, reldir))
        tinfo.name = archpath
        return tinfo
    write_type = 'w:'+zip_type

    if zip_type:
        archive_filename = '{}.tar.{}'.format(archive_fileprefix, zip_type)
    else:
        archive_filename = '{}.tar'.format(archive_fileprefix)

    with tarfile.open(archive_filename, write_type) as out_file:
        for f in flist:
            out_file.add(f, filter=archive_filter)


@click.command()
@click.argument('pvdfile', type=click.Path(exists=True))
@click.argument('files', nargs=-1, type=click.Path(exists=True))
@click.option('--subsetname', '-s', default='soln_subset.pvd',
              help="Name to give to generated subset pvd file")
@click.option('--archive-name', '-a', default='vis_subset',
              type=click.Path(),
              help="Name to give to generated archive")
@click.option('--archive-prefix', '-p', default='',
              help="Directory to prefix archive contents with")
@click.option('--t_step', '-t', default=0.0,
              help="Time step size between selected timesteps")
@click.option('--n_select', '-n', default=0,
              help="Number of timesteps to select by iteration slice")
@click.option('--inc-final/--no-inc-final', default=True,
              help="Whether to ensure the final timestep is included in the "
              "selected set")
@click.option('-d', 'zip_type', flag_value='',
              help="Do not comress archive")
@click.option('-z', 'zip_type', flag_value='gz',
              help="Compress archive using gz")
@click.option('-j', 'zip_type', flag_value='bz2',
              help="Compress archive using bz2")
@click.option('-J', 'zip_type', flag_value='xz', default=True,
              help="Compress archive using xz")
@click.option('--quiet', '-q', is_flag=True,
              help="Do not write to stdout")
def create_subset_archive(pvdfile, files, subsetname,
                          archive_name, archive_prefix, zip_type,
                          t_step, n_select, inc_final,
                          quiet):
    """Generate archive of a subset of the supplied PVDFILE,
    including FILES in archive"""
    rel_dir = os.path.dirname(os.path.normpath(pvdfile))

    subset_fullpath = os.path.join(rel_dir,
                                   subsetname)

    if not quiet:
        click.echo("Generating subset pvd")
    create_subset_pvd(pvdfile, subset_fullpath,
                      nsubset=n_select, t_step=t_step, inc_final=inc_final)

    if not quiet:
        click.echo("Obtaining required file list")
    flist = get_req_file_list_pvd(subset_fullpath)

    flist.extend(files)

    if not quiet:
        with click.progressbar(flist, label="Archiving files") as bar:
            archive_files(archive_name, bar, zip_type, rel_dir,
                          prefix=archive_prefix)
    else:
        archive_files(archive_name, flist, zip_type, rel_dir,
                      prefix=archive_prefix)

if(__name__ == "__main__"):
    create_subset_archive()

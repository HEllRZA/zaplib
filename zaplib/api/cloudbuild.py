from siesta import *
from siesta.auth import APIKeyAuth

from zaplib.configbox import config

class CloudBuildAPI(object):

	def __init__(self, config_id = None):
		auth = APIKeyAuth("Basic %s" % config['api'].cloudbuild, "Authorization")

		self.api = API('https://build-api.cloud.unity3d.com/api/v1/', auth)

		if config_id:
			self.org_id = config[config_id].cloudbuild.org_id
			self.project_id = config[config_id].cloudbuild.project_id
		else:
			self.org_id = None
			self.project_id = None

	def _api_org_prj(self, oid, pid):
		return self.api.orgs(oid).projects(pid)

	def _clean_buildtarget(self, bt):
		target = {k : bt.attrs.get(k, None) for k in ('buildtargetid', 'enabled', 'name', 'platform')}

		if 'builds' in bt.attrs:
			target['build'] = self._clean_build(bt.attrs['builds'][0])

		return target 

	def _clean_build(self, b):
		result = {}
		result['number'] = b['build']
		result['status'] = b['buildStatus']
		result['branch'] = b.get('scmBranch', '')
		result['sha'] = b.get('lastBuiltRevision', '')
		result['platform'] = b['platform']
		result['finish_date'] = b.get('finished', '')
		result['totalTimeInSeconds'] = b.get('totalTimeInSeconds', 0)
		result['download'] = b.get("links",{}).get("download_primary",{}).get("href","")

		return result

	# List all projects 
	# GET /projects
	def get_projects(self):
		
		projects, resp = self.api.projects.get()

		results = []

		for p in projects:
			prj = {k : p.attrs.get(k, None) for k in ('guid', 'name', 'orgid', 'projectid')}
			results.append(prj)

		return results


	# List all build targets for a project
	# GET /orgs/{orgid}/projects/{projectid}/buildtargets
	def get_buildtargets(self, org_id = None, project_id = None, filter = None):
		org_id = self.org_id if not org_id else org_id
		project_id = self.project_id if not project_id else project_id
		
		cb = self._api_org_prj(org_id, project_id)

		args = {
			'include_last_success': "true"
		}

		targets, resp = cb.buildtargets().get(**args)

		results = []

		for t in targets:
			target = self._clean_buildtarget(t)

			if not filter or filter.lower() in target['buildtargetid'].lower():
				results.append(target)

		return results

	# Get a build target
	# GET /orgs/{orgid}/projects/{projectid}/buildtargets/{buildtargetid}
	def get_buildtarget(self, buildtarget_id, org_id = None, project_id = None):
		org_id = self.org_id if not org_id else org_id
		project_id = self.project_id if not project_id else project_id

		cb = self._api_org_prj(org_id, project_id)

		target, resp = cb.buildtargets(buildtarget_id).get()

		result = self._clean_buildtarget(target)

		return target

	# Get a list of builds for a buildtarget
	# GET /orgs/{orgid}/projects/{projectid}/buildtargets/{buildtargetid}/builds
	def get_builds(self, buildtarget_id, org_id = None, project_id = None, per_page=25, page=1):
		org_id = self.org_id if not org_id else org_id
		project_id = self.project_id if not project_id else project_id

		cb = self._api_org_prj(org_id, project_id)

		args = {
			'per_page': per_page,
			'page': page,
			# 'buildStatus': '',
			# 'platform': ''
		}

		builds, resp = cb.buildtargets(buildtarget_id).builds.get(**args)

		result = [self._clean_build(b.attrs) for b in builds]

		return result

	# Build Status
	# GET /orgs/{orgid}/projects/{projectid}/buildtargets/{buildtargetid}/builds/{number}
	def get_buildstatus(self, buildtarget_id, build_num, org_id = None, project_id = None):
		org_id = self.org_id if not org_id else org_id
		project_id = self.project_id if not project_id else project_id

		cb = self._api_org_prj(org_id, project_id)

		build, resp = cb.buildtargets(buildtarget_id).builds(build_num).get()

		if resp.status == 404:
			return None
		else:
			return self._clean_build(build.attrs)


	# Create new build
	# POST /orgs/{orgid}/projects/{projectid}/buildtargets/{buildtargetid}/builds
	def create_build(self, buildtarget_id='_all', org_id = None, project_id = None, commit_hash=None):
		org_id = self.org_id if not org_id else org_id
		project_id = self.project_id if not project_id else project_id

		cb = self._api_org_prj(org_id, project_id)

		args = {
			'clean': True,
			'delay': 0,
			'commit': commit_hash if commit_hash else ''
		}

		builds, resp = cb.buildtargets(buildtarget_id).builds.post_json(**args)

		return [self._clean_build(b.attrs) for b in builds]

	# Cancel all builds
	# DELETE /orgs/{orgid}/projects/{projectid}/buildtargets/{buildtargetid}/builds
	# Cancel all builds in progress for this build target (or all targets, if '_all' is specified as the buildtargetid). Canceling an already finished build will do nothing and respond successfully.
	def cancel_builds(self, buildtarget_id='_all', org_id = None, project_id = None):
		org_id = self.org_id if not org_id else org_id
		project_id = self.project_id if not project_id else project_id

		cb = self._api_org_prj(org_id, project_id)

		build, resp = cb.buildtargets(buildtarget_id).builds.delete()

		return resp.status == 204
		

	# Cancel build
	# DELETE /orgs/{orgid}/projects/{projectid}/buildtargets/{buildtargetid}/builds/{number}
	def cancel_build(self, buildtarget_id, build_num, org_id = None, project_id = None):
		org_id = self.org_id if not org_id else org_id
		project_id = self.project_id if not project_id else project_id

		cb = self._api_org_prj(org_id, project_id)

		build, resp = cb.buildtargets(buildtarget_id).builds(build_num).delete()

		return resp.status == 204

	# Get build share link, or create one.
	# GET /orgs/{orgid}/projects/{projectid}/buildtargets/{buildtargetid}/builds/{number}/share
	def get_or_create_share(self, buildtarget_id, build_num, org_id = None, project_id = None):
		org_id = self.org_id if not org_id else org_id
		project_id = self.project_id if not project_id else project_id

		cb = self._api_org_prj(org_id, project_id)

		share, resp = cb.buildtargets(buildtarget_id).builds(build_num).share.get()

		# if no share link is found, we need to create one.
		if resp.status == 404:
			share, resp = cb.buildtargets(buildtarget_id).builds(build_num).share.post()

			if resp.status == 404: 
				return None

		return "https://developer.cloud.unity3d.com/share/{}/".format(share.attrs['shareid'])



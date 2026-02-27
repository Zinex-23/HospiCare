/**
 * Copyright © 2016-2025 The Thingsboard Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package org.thingsboard.server.service.entitiy.tenant;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;
import org.thingsboard.server.common.data.Tenant;
import org.thingsboard.server.common.data.TenantProfile;
import org.thingsboard.server.common.data.User;
import org.thingsboard.server.common.data.id.TenantId;
import org.thingsboard.server.common.data.security.Authority;
import org.thingsboard.server.common.data.security.UserCredentials;
import org.thingsboard.server.dao.tenant.TbTenantProfileCache;
import org.thingsboard.server.dao.tenant.TenantProfileService;
import org.thingsboard.server.dao.tenant.TenantService;
import org.thingsboard.server.dao.user.UserService;
import org.thingsboard.server.queue.util.TbCoreComponent;
import org.thingsboard.server.service.entitiy.AbstractTbEntityService;
import org.thingsboard.server.service.entitiy.queue.TbQueueService;
import org.thingsboard.server.service.install.InstallScripts;
import org.thingsboard.server.service.sync.vc.EntitiesVersionControlService;

import java.text.Normalizer;
import java.util.Collections;
import java.util.Locale;
import java.util.concurrent.TimeUnit;
import java.util.regex.Pattern;

@Service
@TbCoreComponent
@RequiredArgsConstructor
@Slf4j
public class DefaultTbTenantService extends AbstractTbEntityService implements TbTenantService {

    private static final String DEFAULT_TENANT_ADMIN_PASSWORD = "0702341350";
    private static final String DEFAULT_TENANT_ADMIN_EMAIL_SUFFIX = ".hospicare.dev@gmail.com";
    private static final Pattern SPACES_PATTERN = Pattern.compile("\\s+");
    private static final Pattern NON_ALPHANUMERIC_PATTERN = Pattern.compile("[^a-z0-9]");

    private final TenantService tenantService;
    private final TbTenantProfileCache tenantProfileCache;
    private final InstallScripts installScripts;
    private final TbQueueService tbQueueService;
    private final TenantProfileService tenantProfileService;
    private final EntitiesVersionControlService versionControlService;
    private final UserService userService;
    private final BCryptPasswordEncoder passwordEncoder;

    @Override
    public Tenant save(Tenant tenant) throws Exception {
        boolean created = tenant.getId() == null;
        String tenantTitle = tenant.getTitle();
        Tenant oldTenant = !created ? tenantService.findTenantById(tenant.getId()) : null;

        Tenant savedTenant = tenantService.saveTenant(tenant, tenantId -> {
            installScripts.createDefaultRuleChains(tenantId);
            installScripts.createDefaultEdgeRuleChains(tenantId);
            if (!isTestProfile()) {
                installScripts.createDefaultTenantDashboards(tenantId, null);
            }
            createDefaultTenantAdmin(tenantId, tenantTitle);
        });
        tenantProfileCache.evict(savedTenant.getId());

        TenantProfile oldTenantProfile = oldTenant != null ? tenantProfileService.findTenantProfileById(TenantId.SYS_TENANT_ID, oldTenant.getTenantProfileId()) : null;
        TenantProfile newTenantProfile = tenantProfileService.findTenantProfileById(TenantId.SYS_TENANT_ID, savedTenant.getTenantProfileId());
        tbQueueService.updateQueuesByTenants(Collections.singletonList(savedTenant.getTenantId()), newTenantProfile, oldTenantProfile);
        return savedTenant;
    }

    private void createDefaultTenantAdmin(TenantId tenantId, String tenantTitle) {
        String tenantLocalPart = normalizeTenantTitle(tenantTitle);
        String email = buildAvailableTenantAdminEmail(tenantLocalPart);

        User user = new User();
        user.setAuthority(Authority.TENANT_ADMIN);
        user.setTenantId(tenantId);
        user.setEmail(email);
        User savedUser = userService.saveUser(tenantId, user);

        UserCredentials userCredentials = userService.findUserCredentialsByUserId(TenantId.SYS_TENANT_ID, savedUser.getId());
        userCredentials.setPassword(passwordEncoder.encode(DEFAULT_TENANT_ADMIN_PASSWORD));
        userCredentials.setEnabled(true);
        userCredentials.setActivateToken(null);
        userCredentials.setActivateTokenExpTime(null);
        userService.saveUserCredentials(TenantId.SYS_TENANT_ID, userCredentials);

        log.info("Created default tenant admin account [{}] for tenant [{}]", email, tenantId);
    }

    private String buildAvailableTenantAdminEmail(String tenantLocalPart) {
        int suffix = 0;
        while (true) {
            String email = tenantLocalPart + (suffix == 0 ? "" : suffix) + DEFAULT_TENANT_ADMIN_EMAIL_SUFFIX;
            if (userService.findUserByEmail(TenantId.SYS_TENANT_ID, email) == null) {
                return email;
            }
            suffix++;
        }
    }

    private String normalizeTenantTitle(String tenantTitle) {
        String normalized = Normalizer.normalize(tenantTitle == null ? "" : tenantTitle, Normalizer.Form.NFD);
        normalized = normalized.replaceAll("\\p{M}+", "");
        normalized = normalized.toLowerCase(Locale.ROOT);
        normalized = SPACES_PATTERN.matcher(normalized).replaceAll("");
        normalized = NON_ALPHANUMERIC_PATTERN.matcher(normalized).replaceAll("");
        return normalized.isEmpty() ? "tenant" : normalized;
    }

    @Override
    public void delete(Tenant tenant) throws Exception {
        TenantId tenantId = tenant.getId();
        tenantService.deleteTenant(tenantId);
        tenantProfileCache.evict(tenantId);
        versionControlService.deleteVersionControlSettings(tenantId).get(1, TimeUnit.MINUTES);
    }
}

